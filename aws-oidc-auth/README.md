# aws-oidc-auth

AWS credential helper that exchanges OIDC tokens or AWS Identity Center (SSO) sessions for temporary AWS credentials.

Supports multiple identity providers and federation paths:

| Federation Type | Identity Providers |
|----------------|-------------------|
| **SSO/Identity Center** | AWS IAM Identity Center |
| **Direct STS** (AssumeRoleWithWebIdentity) | Okta, Auth0, Microsoft Entra ID, Cognito User Pool |
| **Cognito Identity Pool** | Okta, Auth0, Microsoft Entra ID, Cognito User Pool |

## Prerequisites

- Go 1.24+
- A configured `config.json`

## Build

```bash
make macos-arm64    # Apple Silicon
make macos-intel    # Intel Mac
make linux-x64      # Linux AMD64
make linux-arm64    # Linux ARM64
make windows        # Windows AMD64
make all            # All platforms
```

## Install

Copy the binary and your `config.json` to `~/aws-oidc-auth/`:

```bash
mkdir -p ~/aws-oidc-auth
cp bin/credential-process-macos-arm64 ~/aws-oidc-auth/credential-process
cp config.json ~/aws-oidc-auth/
```

Then configure your AWS profile in `~/.aws/config`:

```ini
[profile bedrock]
credential_process = /Users/you/aws-oidc-auth/credential-process --profile default
region = us-west-2
```

## Usage

```bash
# Normal mode (called by AWS CLI/SDK automatically)
credential-process --profile default

# Check if cached credentials are still valid
credential-process --check-expiration --profile default

# Refresh credentials if expired (for cron jobs, session storage only)
credential-process --refresh-if-needed --profile default

# Clear cached credentials and force re-authentication
credential-process --clear-cache --profile default

# Store Azure AD client secret in OS keyring
credential-process --set-client-secret --profile default

# Debug mode
AWS_OIDC_AUTH_DEBUG=1 credential-process --profile default
```

## Configuration

The binary reads `config.json` from the same directory as the binary, or from `~/aws-oidc-auth/config.json`.

### SSO / Identity Center

```json
{
  "profiles": {
    "default": {
      "federation_type": "sso",
      "sso_start_url": "https://d-xxxxxxxxxx.awsapps.com/start",
      "sso_region": "us-east-1",
      "sso_account_id": "123456789012",
      "sso_role_name": "MyPermissionSet",
      "aws_region": "us-west-2",
      "credential_storage": "session"
    }
  }
}
```

### Direct STS (OIDC → AssumeRoleWithWebIdentity)

```json
{
  "profiles": {
    "default": {
      "provider_domain": "login.microsoftonline.com/tenant-id/v2.0",
      "client_id": "your-client-id",
      "provider_type": "auto",
      "aws_region": "us-east-1",
      "credential_storage": "session",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/MyRole"
    }
  }
}
```

### Cognito Identity Pool

```json
{
  "profiles": {
    "default": {
      "provider_domain": "dev-12345.okta.com",
      "client_id": "your-client-id",
      "provider_type": "auto",
      "aws_region": "us-east-1",
      "credential_storage": "session",
      "federation_type": "cognito",
      "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
  }
}
```

## Configuration Reference

| Field | Description |
|-------|-------------|
| `federation_type` | `sso`, `direct` (STS), or `cognito` (Identity Pool). Auto-detected if omitted. |
| `provider_domain` | OIDC provider domain (not needed for SSO) |
| `client_id` | OAuth2 client ID (not needed for SSO) |
| `provider_type` | `okta`, `auth0`, `azure`, `cognito`, or `auto` (detect from known domains; unknown domains must be set explicitly) |
| `aws_region` | AWS region for STS/Cognito/SSO calls |
| `credential_storage` | `session` (file) or `keyring` (OS secure storage) |
| `sso_start_url` | AWS SSO start URL (SSO mode) |
| `sso_region` | AWS SSO region (SSO mode, defaults to `aws_region`) |
| `sso_account_id` | AWS account ID (SSO mode) |
| `sso_role_name` | Permission set / role name (SSO mode) |
| `federated_role_arn` | IAM role ARN (direct mode) |
| `identity_pool_id` | Cognito Identity Pool ID (cognito mode) |
| `azure_auth_mode` | `certificate`, `secret`, or empty (public client) |
| `client_certificate_path` | Path to PEM certificate (certificate mode) |
| `client_certificate_key_path` | Path to PEM private key (certificate mode) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AWS_OIDC_AUTH_PROFILE` | Override the default profile name |
| `AWS_OIDC_AUTH_DEBUG` | Set to `1` for debug output |
| `AWS_OIDC_AUTH_CLIENT_SECRET` | Provide Azure AD client secret via env |
| `AWS_OIDC_AUTH_MONITORING_TOKEN` | Provide monitoring token directly |

## Tests

```bash
make test
```

## Architecture

```
cmd/credential-process/   Entry point and orchestration
internal/
  azure/       Azure AD confidential client (JWT assertion, secret management)
  browser/     Cross-platform browser opener
  config/      Config file loading and profile management
  federation/  AWS credential exchange (STS + Cognito)
  jwt/         JWT decode (no verification)
  oidc/        OAuth2 authorization code flow with PKCE
  portlock/    Port-based locking to prevent concurrent auth
  provider/    OIDC provider detection from domain
  sso/         AWS Identity Center device auth flow + credential retrieval
  storage/     Credential caching (keyring + session file)
```
