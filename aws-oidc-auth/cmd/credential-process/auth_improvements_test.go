package main

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"

	"aws-oidc-auth/internal/config"
	"aws-oidc-auth/internal/federation"
	"aws-oidc-auth/internal/jwt"
	"aws-oidc-auth/internal/oidc"
	"aws-oidc-auth/internal/storage"
)

func captureStdout(t *testing.T, fn func() int) (int, string) {
	t.Helper()

	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("os.Pipe: %v", err)
	}
	defer r.Close()

	oldStdout := os.Stdout
	os.Stdout = w
	code := fn()
	w.Close()
	os.Stdout = oldStdout

	out, err := io.ReadAll(r)
	if err != nil {
		t.Fatalf("ReadAll(stdout): %v", err)
	}

	return code, string(out)
}

func makeJWT(t *testing.T, claims map[string]interface{}) string {
	t.Helper()

	header := base64.RawURLEncoding.EncodeToString([]byte(`{"alg":"none","typ":"JWT"}`))
	payloadBytes, err := json.Marshal(claims)
	if err != nil {
		t.Fatalf("Marshal(claims): %v", err)
	}
	payload := base64.RawURLEncoding.EncodeToString(payloadBytes)
	return header + "." + payload + ".signature"
}

func TestResolveProviderType_AutoRequiresKnownProvider(t *testing.T) {
	_, err := resolveProviderType(&config.ProfileConfig{
		ProviderType:   "auto",
		ProviderDomain: "example.com",
	})
	if err == nil {
		t.Fatal("expected error for unknown auto-detected provider")
	}
	if !strings.Contains(err.Error(), "could not auto-detect provider type") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestResolveProviderType_RejectsUnsupportedExplicitProvider(t *testing.T) {
	_, err := resolveProviderType(&config.ProfileConfig{
		ProviderType: "oidc",
	})
	if err == nil {
		t.Fatal("expected error for unsupported explicit provider")
	}
	if !strings.Contains(err.Error(), "unsupported provider_type") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestBuildTokenURL_AzureTrimsVersionSuffix(t *testing.T) {
	got, err := buildTokenURL("login.microsoftonline.com/tenant-id/v2.0", "azure")
	if err != nil {
		t.Fatalf("buildTokenURL: %v", err)
	}

	want := "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token"
	if got != want {
		t.Fatalf("buildTokenURL() = %q, want %q", got, want)
	}
}

func TestRunOIDC_UsesCachedCredentialsAfterBusyPort(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	holder, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("Listen: %v", err)
	}
	defer holder.Close()

	port := holder.Addr().(*net.TCPAddr).Port

	oldPort := defaultRedirectPort
	oldWaitTimeout := oidcPortWaitTimeout
	oldAuth := oidcAuthenticateWithOpts
	defaultRedirectPort = port
	oidcPortWaitTimeout = 2 * time.Second
	oidcAuthenticateWithOpts = func(*oidc.AuthOptions) (*oidc.AuthResult, error) {
		return nil, errors.New("unexpected browser auth")
	}
	t.Cleanup(func() {
		defaultRedirectPort = oldPort
		oidcPortWaitTimeout = oldWaitTimeout
		oidcAuthenticateWithOpts = oldAuth
	})

	errCh := make(chan error, 1)
	go func() {
		time.Sleep(200 * time.Millisecond)
		errCh <- storage.SaveToCredentialsFile(&federation.AWSCredentials{
			Version:         1,
			AccessKeyID:     "AKIDWAIT",
			SecretAccessKey: "SECRETWAIT",
			SessionToken:    "TOKENWAIT",
			Expiration:      time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339),
		}, "default")
		_ = holder.Close()
	}()

	cfg := &config.ProfileConfig{
		ProviderDomain:    "dev-123.okta.com",
		ClientID:          "client",
		ProviderType:      "okta",
		AWSRegion:         "us-east-1",
		CredentialStorage: "session",
		FederationType:    "cognito",
		IdentityPoolID:    "us-east-1:pool",
	}

	code, stdout := captureStdout(t, func() int {
		return runOIDC("default", cfg)
	})
	if code != 0 {
		t.Fatalf("runOIDC() exit = %d, want 0", code)
	}
	if err := <-errCh; err != nil {
		t.Fatalf("SaveToCredentialsFile during wait: %v", err)
	}

	var creds federation.AWSCredentials
	if err := json.Unmarshal([]byte(stdout), &creds); err != nil {
		t.Fatalf("stdout is not credential JSON: %v\nraw: %s", err, stdout)
	}
	if creds.AccessKeyID != "AKIDWAIT" {
		t.Fatalf("AccessKeyID = %q, want %q", creds.AccessKeyID, "AKIDWAIT")
	}
}

func TestRunOIDC_ContinuesAuthAfterBusyPortWithoutCachedCredentials(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	holder, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("Listen: %v", err)
	}
	defer holder.Close()

	port := holder.Addr().(*net.TCPAddr).Port

	oldPort := defaultRedirectPort
	oldWaitTimeout := oidcPortWaitTimeout
	oldAuth := oidcAuthenticateWithOpts
	oldAssume := assumeRoleWithWebIdentity
	defaultRedirectPort = port
	oidcPortWaitTimeout = 2 * time.Second

	authClaims := jwt.Claims{
		"exp": float64(time.Now().Add(1 * time.Hour).Unix()),
		"sub": "carol",
	}
	authCalled := false
	oidcAuthenticateWithOpts = func(*oidc.AuthOptions) (*oidc.AuthResult, error) {
		authCalled = true
		return &oidc.AuthResult{
			IDToken:     makeJWT(t, map[string]interface{}(authClaims)),
			TokenClaims: authClaims,
		}, nil
	}
	assumeRoleWithWebIdentity = func(region, roleARN, token string, tokenClaims jwt.Claims, maxDuration int) (*federation.AWSCredentials, error) {
		if tokenClaims.GetString("sub") != "carol" {
			t.Fatalf("sub claim = %q, want %q", tokenClaims.GetString("sub"), "carol")
		}
		return &federation.AWSCredentials{
			Version:         1,
			AccessKeyID:     "AKIDBUSYAUTH",
			SecretAccessKey: "SECRETBUSYAUTH",
			SessionToken:    "TOKENBUSYAUTH",
			Expiration:      time.Now().Add(1 * time.Hour).UTC().Format(time.RFC3339),
		}, nil
	}
	t.Cleanup(func() {
		defaultRedirectPort = oldPort
		oidcPortWaitTimeout = oldWaitTimeout
		oidcAuthenticateWithOpts = oldAuth
		assumeRoleWithWebIdentity = oldAssume
	})

	go func() {
		time.Sleep(200 * time.Millisecond)
		_ = holder.Close()
	}()

	cfg := &config.ProfileConfig{
		ProviderDomain:    "dev-123.okta.com",
		ClientID:          "client",
		ProviderType:      "okta",
		AWSRegion:         "us-east-1",
		CredentialStorage: "session",
		FederationType:    "direct",
		FederatedRoleARN:  "arn:aws:iam::123456789012:role/TestRole",
	}

	code, stdout := captureStdout(t, func() int {
		return runOIDC("default", cfg)
	})
	if code != 0 {
		t.Fatalf("runOIDC() exit = %d, want 0", code)
	}
	if !authCalled {
		t.Fatal("expected browser auth after the redirect port became available")
	}

	var creds federation.AWSCredentials
	if err := json.Unmarshal([]byte(stdout), &creds); err != nil {
		t.Fatalf("stdout is not credential JSON: %v\nraw: %s", err, stdout)
	}
	if creds.AccessKeyID != "AKIDBUSYAUTH" {
		t.Fatalf("AccessKeyID = %q, want %q", creds.AccessKeyID, "AKIDBUSYAUTH")
	}
}

func TestTrySilentRefresh_UsesCachedMonitoringToken(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	oldAssume := assumeRoleWithWebIdentity
	t.Cleanup(func() {
		assumeRoleWithWebIdentity = oldAssume
	})

	claims := map[string]interface{}{
		"exp": float64(time.Now().Add(1 * time.Hour).Unix()),
		"sub": "alice",
	}
	idToken := makeJWT(t, claims)
	if err := storage.SaveMonitoringToken("default", "session", idToken, claims); err != nil {
		t.Fatalf("SaveMonitoringToken: %v", err)
	}

	assumeRoleWithWebIdentity = func(region, roleARN, token string, tokenClaims jwt.Claims, maxDuration int) (*federation.AWSCredentials, error) {
		if region != "us-east-1" {
			t.Fatalf("region = %q, want %q", region, "us-east-1")
		}
		if roleARN != "arn:aws:iam::123456789012:role/TestRole" {
			t.Fatalf("roleARN = %q", roleARN)
		}
		if token != idToken {
			t.Fatalf("token = %q, want cached token", token)
		}
		if tokenClaims.GetString("sub") != "alice" {
			t.Fatalf("sub claim = %q, want %q", tokenClaims.GetString("sub"), "alice")
		}
		return &federation.AWSCredentials{
			Version:         1,
			AccessKeyID:     "AKIDSILENT",
			SecretAccessKey: "SECRETSILENT",
			SessionToken:    "TOKENSILENT",
			Expiration:      time.Now().Add(45 * time.Minute).UTC().Format(time.RFC3339),
		}, nil
	}

	cfg := &config.ProfileConfig{
		AWSRegion:          "us-east-1",
		CredentialStorage:  "session",
		FederationType:     "direct",
		FederatedRoleARN:   "arn:aws:iam::123456789012:role/TestRole",
		MaxSessionDuration: 3600,
	}

	creds, err := trySilentRefresh("default", cfg, "okta")
	if err != nil {
		t.Fatalf("trySilentRefresh: %v", err)
	}
	if creds == nil {
		t.Fatal("expected silently refreshed credentials")
	}
	if creds.AccessKeyID != "AKIDSILENT" {
		t.Fatalf("AccessKeyID = %q, want %q", creds.AccessKeyID, "AKIDSILENT")
	}

	saved, err := storage.ReadFromCredentialsFile("default")
	if err != nil {
		t.Fatalf("ReadFromCredentialsFile: %v", err)
	}
	if saved == nil || saved.AccessKeyID != "AKIDSILENT" {
		t.Fatalf("saved credentials = %+v, want AKIDSILENT", saved)
	}
}

func TestTryRefreshToken_UsesStoredRefreshToken(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)
	t.Setenv("AWS_OIDC_AUTH_MONITORING_TOKEN", "")

	oldRefresh := oidcRefreshTokenExchangeOpts
	oldAssume := assumeRoleWithWebIdentity
	oidcRefreshTokenExchangeOpts = func(tokenURL, refreshToken, clientID string, opts *oidc.ConfidentialClientOpts) (*oidc.TokenResponse, error) {
		if tokenURL != "https://dev-123.okta.com/oauth2/v1/token" {
			t.Fatalf("tokenURL = %q", tokenURL)
		}
		if refreshToken != "refresh-token-old" {
			t.Fatalf("refreshToken = %q", refreshToken)
		}
		if clientID != "client-id" {
			t.Fatalf("clientID = %q", clientID)
		}
		if opts != nil {
			t.Fatalf("expected nil confidential options for okta refresh, got %#v", opts)
		}

		claims := map[string]interface{}{
			"exp": float64(time.Now().Add(1 * time.Hour).Unix()),
			"sub": "bob",
		}
		return &oidc.TokenResponse{
			IDToken:      makeJWT(t, claims),
			RefreshToken: "refresh-token-new",
		}, nil
	}
	assumeRoleWithWebIdentity = func(region, roleARN, token string, tokenClaims jwt.Claims, maxDuration int) (*federation.AWSCredentials, error) {
		if tokenClaims.GetString("sub") != "bob" {
			t.Fatalf("sub claim = %q, want %q", tokenClaims.GetString("sub"), "bob")
		}
		return &federation.AWSCredentials{
			Version:         1,
			AccessKeyID:     "AKIDREFRESH",
			SecretAccessKey: "SECRETREFRESH",
			SessionToken:    "TOKENREFRESH",
			Expiration:      time.Now().Add(30 * time.Minute).UTC().Format(time.RFC3339),
		}, nil
	}
	t.Cleanup(func() {
		oidcRefreshTokenExchangeOpts = oldRefresh
		assumeRoleWithWebIdentity = oldAssume
	})

	if err := storage.SaveRefreshToken("default", "session", "refresh-token-old"); err != nil {
		t.Fatalf("SaveRefreshToken: %v", err)
	}

	cfg := &config.ProfileConfig{
		ProviderDomain:     "dev-123.okta.com",
		ClientID:           "client-id",
		AWSRegion:          "us-east-1",
		CredentialStorage:  "session",
		FederationType:     "direct",
		FederatedRoleARN:   "arn:aws:iam::123456789012:role/TestRole",
		MaxSessionDuration: 3600,
	}

	creds, err := tryRefreshToken("default", cfg, "okta")
	if err != nil {
		t.Fatalf("tryRefreshToken: %v", err)
	}
	if creds == nil {
		t.Fatal("expected refreshed credentials")
	}
	if creds.AccessKeyID != "AKIDREFRESH" {
		t.Fatalf("AccessKeyID = %q, want %q", creds.AccessKeyID, "AKIDREFRESH")
	}

	if got := storage.LoadRefreshToken("default", "session"); got != "refresh-token-new" {
		t.Fatalf("LoadRefreshToken() = %q, want %q", got, "refresh-token-new")
	}
	token, err := storage.GetMonitoringToken("default", "session")
	if err != nil {
		t.Fatalf("GetMonitoringToken: %v", err)
	}
	if token == "" {
		t.Fatal("expected refreshed monitoring token to be cached")
	}
}

func TestTryRefreshToken_RetainsStoredRefreshTokenOnTransientError(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	oldRefresh := oidcRefreshTokenExchangeOpts
	oidcRefreshTokenExchangeOpts = func(tokenURL, refreshToken, clientID string, opts *oidc.ConfidentialClientOpts) (*oidc.TokenResponse, error) {
		return nil, errors.New("temporary outage")
	}
	t.Cleanup(func() {
		oidcRefreshTokenExchangeOpts = oldRefresh
	})

	if err := storage.SaveRefreshToken("default", "session", "refresh-token-old"); err != nil {
		t.Fatalf("SaveRefreshToken: %v", err)
	}

	cfg := &config.ProfileConfig{
		ProviderDomain:    "dev-123.okta.com",
		ClientID:          "client-id",
		CredentialStorage: "session",
	}

	creds, err := tryRefreshToken("default", cfg, "okta")
	if err == nil {
		t.Fatal("expected refresh token exchange to fail")
	}
	if creds != nil {
		t.Fatal("expected no credentials on transient refresh failure")
	}
	if got := storage.LoadRefreshToken("default", "session"); got != "refresh-token-old" {
		t.Fatalf("LoadRefreshToken() = %q, want %q", got, "refresh-token-old")
	}
}

func TestTryRefreshToken_ClearsStoredRefreshTokenOnInvalidGrant(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	t.Setenv("USERPROFILE", tmp)

	oldRefresh := oidcRefreshTokenExchangeOpts
	oidcRefreshTokenExchangeOpts = func(tokenURL, refreshToken, clientID string, opts *oidc.ConfidentialClientOpts) (*oidc.TokenResponse, error) {
		return nil, &oidc.TokenExchangeError{
			Operation:  "refresh token exchange",
			StatusCode: http.StatusBadRequest,
			Body:       `{"error":"invalid_grant"}`,
		}
	}
	t.Cleanup(func() {
		oidcRefreshTokenExchangeOpts = oldRefresh
	})

	if err := storage.SaveRefreshToken("default", "session", "refresh-token-old"); err != nil {
		t.Fatalf("SaveRefreshToken: %v", err)
	}

	cfg := &config.ProfileConfig{
		ProviderDomain:    "dev-123.okta.com",
		ClientID:          "client-id",
		CredentialStorage: "session",
	}

	creds, err := tryRefreshToken("default", cfg, "okta")
	if err == nil {
		t.Fatal("expected refresh token exchange to fail")
	}
	if creds != nil {
		t.Fatal("expected no credentials on invalid_grant")
	}
	if got := storage.LoadRefreshToken("default", "session"); got != "" {
		t.Fatalf("LoadRefreshToken() = %q, want empty string", got)
	}
}
