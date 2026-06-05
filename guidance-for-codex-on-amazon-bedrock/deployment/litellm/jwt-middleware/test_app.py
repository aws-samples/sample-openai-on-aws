"""
Tests for jwt-middleware app.py

Uses moto to mock DynamoDB and responses to mock HTTP calls, so no real AWS
credentials or external network access is required.
"""
import importlib
import json
import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from moto import mock_aws

# ---------------------------------------------------------------------------
# Helpers to generate RS256 key pair and test JWTs
# ---------------------------------------------------------------------------

def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


def make_jwt(private_key, kid="test-kid", claims_override=None, expired=False):
    import jwt as pyjwt
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(seconds=10) if expired else now + timedelta(hours=1)
    payload = {
        "sub": "user-123",
        "email": "user@example.com",
        "name": "Test User",
        "groups": ["engineers"],
        "iss": "https://idp.example.com",
        "aud": "test-audience",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if claims_override:
        payload.update(claims_override)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pyjwt.encode(payload, pem, algorithm="RS256", headers={"kid": kid})


def build_jwks(public_key, kid="test-kid"):
    """Return a JWKS dict containing the given public key."""
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    from cryptography.hazmat.primitives import serialization
    import base64, struct

    pub_numbers = public_key.public_key().public_numbers() if hasattr(public_key, 'public_key') else public_key.public_numbers()

    def int_to_base64url(n):
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

    return {
        "keys": [{
            "kty": "RSA",
            "kid": kid,
            "use": "sig",
            "alg": "RS256",
            "n": int_to_base64url(pub_numbers.n),
            "e": int_to_base64url(pub_numbers.e),
        }]
    }


# ---------------------------------------------------------------------------
# Fixture: import app with mocked environment and AWS
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rsa_keys():
    private_key, public_key = generate_rsa_key_pair()
    return private_key, public_key


@pytest.fixture()
def app_client(rsa_keys, monkeypatch):
    """
    Yields a Flask test client with:
    - moto mocking DynamoDB
    - env vars set to plausible values
    - JWKS endpoint mocked via patch
    """
    private_key, public_key = rsa_keys
    jwks = build_jwks(public_key)

    env = {
        "JWKS_URL": "https://idp.example.com/.well-known/jwks.json",
        "JWT_AUDIENCE": "test-audience",
        "JWT_ISSUER": "https://idp.example.com",
        "LITELLM_URL": "http://litellm:4000",
        "LITELLM_MASTER_KEY": "master-key-test",
        "DYNAMODB_TABLE": "codex-user-keys",
        "AWS_REGION": "us-east-1",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    with mock_aws():
        # Create the DynamoDB table that app.py expects
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="codex-user-keys",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Force fresh module import so it picks up mocked env + DynamoDB
        if "app" in sys.modules:
            del sys.modules["app"]

        with patch("requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = jwks
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            import app as flask_app

            # Clear lru_cache so each test fixture gets a fresh JWKS fetch
            flask_app.get_jwks.cache_clear()
            flask_app.jwks_cache.clear()
            flask_app.user_key_cache.clear()

            flask_app.app.config["TESTING"] = True
            client = flask_app.app.test_client()
            yield client, flask_app, private_key


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self, app_client):
        client, _, _ = app_client
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# JWT validation
# ---------------------------------------------------------------------------

class TestJWTValidation:
    def test_missing_auth_header_returns_401(self, app_client):
        client, _, _ = app_client
        resp = client.get("/api/my-key")
        assert resp.status_code == 401
        assert "Missing or invalid" in resp.get_json()["error"]

    def test_non_bearer_token_returns_401(self, app_client):
        client, _, _ = app_client
        resp = client.get("/api/my-key", headers={"Authorization": "Basic abc"})
        assert resp.status_code == 401

    def test_invalid_jwt_returns_401(self, app_client):
        client, _, _ = app_client
        resp = client.get("/api/my-key", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_expired_jwt_returns_401(self, app_client, rsa_keys):
        client, flask_app, private_key = app_client
        token = make_jwt(private_key, expired=True)
        flask_app.get_jwks.cache_clear()

        resp = client.get("/api/my-key", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert "expired" in resp.get_json()["error"].lower()

    def test_token_without_sub_returns_401(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        token = make_jwt(private_key, claims_override={"sub": None})
        # sub=None still sets the key; need to remove it entirely
        import jwt as pyjwt
        from datetime import datetime, timezone, timedelta
        from cryptography.hazmat.primitives import serialization
        now = datetime.now(tz=timezone.utc)
        payload = {
            "email": "user@example.com",
            "iss": "https://idp.example.com",
            "aud": "test-audience",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        token = pyjwt.encode(payload, pem, algorithm="RS256", headers={"kid": "test-kid"})
        resp = client.get("/api/my-key", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# validate_jwt_token unit tests (direct calls)
# ---------------------------------------------------------------------------

class TestValidateJwtToken:
    def test_valid_token_returns_user_info(self, app_client):
        _, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        token = make_jwt(private_key)
        info = flask_app.validate_jwt_token(token)
        assert info["user_id"] == "user-123"
        assert info["email"] == "user@example.com"
        assert info["groups"] == ["engineers"]

    def test_no_jwks_url_raises(self, app_client, monkeypatch):
        _, flask_app, private_key = app_client
        monkeypatch.setattr(flask_app, "JWKS_URL", None)
        with pytest.raises(ValueError, match="JWKS_URL"):
            flask_app.validate_jwt_token("any.token.value")

    def test_unknown_kid_raises(self, app_client):
        _, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        token = make_jwt(private_key, kid="unknown-kid")
        with pytest.raises(ValueError, match="not found in JWKS"):
            flask_app.validate_jwt_token(token)


# ---------------------------------------------------------------------------
# API key caching (DynamoDB + in-memory)
# ---------------------------------------------------------------------------

class TestApiKeyCaching:
    def test_get_cached_api_key_returns_none_when_absent(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache.clear()
        result = flask_app.get_cached_api_key("nonexistent-user")
        assert result is None

    def test_cache_and_retrieve_api_key(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache.clear()
        user_info = {"user_id": "u-1", "email": "u@example.com", "name": "U", "groups": []}
        flask_app.cache_api_key("u-1", "sk-test-key", user_info)
        assert flask_app.get_cached_api_key("u-1") == "sk-test-key"

    def test_in_memory_cache_hit_skips_dynamodb(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache["cached-user"] = "sk-cached"
        result = flask_app.get_cached_api_key("cached-user")
        assert result == "sk-cached"


# ---------------------------------------------------------------------------
# /api/my-key endpoint (get_or_create flow)
# ---------------------------------------------------------------------------

class TestGetMyKey:
    def _auth_header(self, private_key):
        return {"Authorization": f"Bearer {make_jwt(private_key)}"}

    def test_returns_api_key_for_valid_jwt_new_user(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        flask_app.user_key_cache.clear()

        with patch.object(flask_app, "create_litellm_api_key", return_value="sk-new-key"):
            resp = client.get("/api/my-key", headers=self._auth_header(private_key))

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["api_key"] == "sk-new-key"
        assert data["email"] == "user@example.com"

    def test_returns_cached_key_for_known_user(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        flask_app.user_key_cache["user-123"] = "sk-cached-key"

        resp = client.get("/api/my-key", headers=self._auth_header(private_key))
        assert resp.status_code == 200
        assert resp.get_json()["api_key"] == "sk-cached-key"

    def test_returns_500_when_key_creation_fails(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        flask_app.user_key_cache.clear()

        with patch.object(flask_app, "create_litellm_api_key", side_effect=Exception("LiteLLM down")):
            resp = client.get("/api/my-key", headers=self._auth_header(private_key))

        assert resp.status_code == 500
        assert "Key management failed" in resp.get_json()["error"]


# ---------------------------------------------------------------------------
# Proxy endpoint
# ---------------------------------------------------------------------------

class TestProxy:
    def _auth_header(self, private_key):
        return {"Authorization": f"Bearer {make_jwt(private_key)}"}

    def test_proxy_forwards_request_to_litellm(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        flask_app.user_key_cache["user-123"] = "sk-proxy-key"

        mock_litellm_resp = MagicMock()
        mock_litellm_resp.status_code = 200
        mock_litellm_resp.headers = {"Content-Type": "application/json"}
        mock_litellm_resp.iter_content = MagicMock(return_value=[b'{"result":"ok"}'])

        with patch.object(flask_app.session, "request", return_value=mock_litellm_resp) as mock_req:
            resp = client.post(
                "/v1/chat/completions",
                headers={**self._auth_header(private_key), "Content-Type": "application/json"},
                json={"model": "gpt-4", "messages": []},
            )

        assert resp.status_code == 200
        # Verify the upstream call used the user's LiteLLM key
        call_headers = mock_req.call_args.kwargs["headers"]
        assert call_headers["Authorization"] == "Bearer sk-proxy-key"

    def test_proxy_returns_401_without_auth(self, app_client):
        client, _, _ = app_client
        resp = client.post("/v1/chat/completions", json={})
        assert resp.status_code == 401

    def test_proxy_returns_500_on_litellm_failure(self, app_client):
        client, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        flask_app.user_key_cache["user-123"] = "sk-key"

        with patch.object(flask_app.session, "request", side_effect=Exception("connection refused")):
            resp = client.get("/v1/models", headers=self._auth_header(private_key))

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# create_litellm_api_key unit tests
# ---------------------------------------------------------------------------

class TestCreateLitellmApiKey:
    def test_returns_key_on_success(self, app_client):
        _, flask_app, _ = app_client
        user_info = {"user_id": "u-2", "email": "u2@example.com", "name": "U2", "groups": []}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"key": "sk-created"}
        mock_resp.raise_for_status = MagicMock()

        with patch.object(flask_app.session, "post", return_value=mock_resp):
            key = flask_app.create_litellm_api_key(user_info)

        assert key == "sk-created"

    def test_raises_when_key_missing_in_response(self, app_client):
        _, flask_app, _ = app_client
        user_info = {"user_id": "u-3", "email": "u3@example.com", "name": "U3", "groups": []}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}  # no "key" field
        mock_resp.raise_for_status = MagicMock()

        with patch.object(flask_app.session, "post", return_value=mock_resp):
            with pytest.raises(Exception, match="did not return an API key"):
                flask_app.create_litellm_api_key(user_info)

    def test_raises_on_409_conflict(self, app_client):
        _, flask_app, _ = app_client
        user_info = {"user_id": "u-4", "email": "u4@example.com", "name": "U4", "groups": []}

        import requests as req_lib
        http_err = req_lib.exceptions.HTTPError(response=MagicMock(status_code=409))
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = http_err

        with patch.object(flask_app.session, "post", return_value=mock_resp):
            with pytest.raises(Exception, match="Key already exists"):
                flask_app.create_litellm_api_key(user_info)

    def test_raises_on_non_409_http_error(self, app_client):
        _, flask_app, _ = app_client
        user_info = {"user_id": "u-5", "email": "u5@example.com", "name": "U5", "groups": []}

        import requests as req_lib
        http_err = req_lib.exceptions.HTTPError(response=MagicMock(status_code=500))
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = http_err

        with patch.object(flask_app.session, "post", return_value=mock_resp):
            with pytest.raises(Exception, match="Failed to create API key"):
                flask_app.create_litellm_api_key(user_info)


# ---------------------------------------------------------------------------
# Additional edge case coverage
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_get_jwks_raises_on_fetch_failure(self, app_client):
        _, flask_app, _ = app_client
        flask_app.get_jwks.cache_clear()
        with patch.object(flask_app.session, "get", side_effect=Exception("network error")):
            with pytest.raises(Exception, match="network error"):
                flask_app.get_jwks()

    def test_validate_jwt_token_missing_kid_raises(self, app_client):
        _, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        import jwt as pyjwt
        from datetime import datetime, timezone, timedelta
        from cryptography.hazmat.primitives import serialization
        now = datetime.now(tz=timezone.utc)
        payload = {
            "sub": "u", "email": "u@x.com", "iss": "https://idp.example.com",
            "aud": "test-audience",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
        # Encode without kid header
        token = pyjwt.encode(payload, pem, algorithm="RS256")
        with pytest.raises(ValueError, match="missing 'kid'"):
            flask_app.validate_jwt_token(token)

    def test_validate_jwt_wrong_audience_raises(self, app_client):
        _, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        token = make_jwt(private_key, claims_override={"aud": "wrong-audience"})
        with pytest.raises(ValueError, match="Invalid audience|Invalid JWT"):
            flask_app.validate_jwt_token(token)

    def test_validate_jwt_wrong_issuer_raises(self, app_client):
        _, flask_app, private_key = app_client
        flask_app.get_jwks.cache_clear()
        token = make_jwt(private_key, claims_override={"iss": "https://evil.com"})
        with pytest.raises(ValueError, match="Invalid issuer|Invalid JWT"):
            flask_app.validate_jwt_token(token)

    def test_get_cached_api_key_dynamodb_error_returns_none(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache.clear()
        with patch.object(flask_app.user_key_table, "get_item", side_effect=Exception("DynamoDB down")):
            result = flask_app.get_cached_api_key("any-user")
        assert result is None

    def test_get_cached_api_key_found_in_dynamodb(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache.clear()
        with patch.object(flask_app.user_key_table, "get_item",
                          return_value={"Item": {"user_id": "db-user", "api_key": "sk-from-db"}}):
            result = flask_app.get_cached_api_key("db-user")
        assert result == "sk-from-db"
        assert flask_app.user_key_cache.get("db-user") == "sk-from-db"

    def test_cache_api_key_dynamodb_error_is_swallowed(self, app_client):
        _, flask_app, _ = app_client
        flask_app.user_key_cache.clear()
        user_info = {"user_id": "err-user", "email": "e@x.com", "name": "E", "groups": []}
        with patch.object(flask_app.user_key_table, "put_item", side_effect=Exception("write error")):
            flask_app.cache_api_key("err-user", "sk-x", user_info)
        # In-memory cache should still be set
        assert flask_app.user_key_cache.get("err-user") == "sk-x"
