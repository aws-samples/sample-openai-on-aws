# AWS OIDC Auth Helper

A standalone credential helper binary that authenticates users via OIDC or AWS Identity Center (SSO) and returns temporary AWS credentials. It implements the [credential_process](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html) protocol, so any AWS SDK or tool that reads `~/.aws/config` can use it — no AWS CLI installation required.

## Supported federation paths

| Federation Type | Identity Providers |
|---|---|
| AWS SSO / Identity Center | AWS IAM Identity Center (device auth flow) |
| Direct STS (AssumeRoleWithWebIdentity) | Okta, Auth0, Microsoft Entra ID, Cognito User Pool |
| Cognito Identity Pool | Okta, Auth0, Microsoft Entra ID, Cognito User Pool |

## Prerequisites

- Go 1.24+ (build only — the compiled binary has no runtime dependencies)
- A configured identity provider (Okta app, Entra ID app registration, Identity Center instance, etc.)
- The corresponding AWS-side federation resource (IAM role with trust policy, Cognito Identity Pool, or SSO permission set)
- A default web browser (used for interactive login flows)
- **Windows**: no additional runtime dependencies; credential storage uses Windows Credential Manager

## Build

From `aws-oidc-auth/`:

### macOS / Linux

```bash
make macos-arm64    # Apple Silicon
make macos-intel    # Intel Mac
make linux-x64      # Linux AMD64
make linux-arm64    # Linux ARM64
make all            # All platforms
```

### Windows

```bash
make windows        # Windows AMD64
```

Or build directly with Go (works from PowerShell or CMD):

```powershell
$env:CGO_ENABLED="0"; $env:GOOS="windows"; $env:GOARCH="amd64"
go build -ldflags "-s -w" -o bin\credential-process.exe .\cmd\credential-process\
```

Binaries are written to `aws-oidc-auth/bin/`.

To run tests:

```bash
make test
```

## Install

### macOS / Linux

1. Create the install directory and copy the binary:

```bash
mkdir -p ~/aws-oidc-auth
cp aws-oidc-auth/bin/credential-process-macos-arm64 ~/aws-oidc-auth/credential-process
chmod +x ~/aws-oidc-auth/credential-process
```

2. Create `~/aws-oidc-auth/config.json` with your profile (see Configuration below).

3. Add a profile to `~/.aws/config` that points to the binary:

```ini
[profile bedrock]
credential_process = /Users/you/aws-oidc-auth/credential-process --profile default
region = us-west-2
```

### Windows

1. Create the install directory and copy the binary:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\aws-oidc-auth"
Copy-Item source\aws-oidc-auth\bin\credential-process.exe "$env:USERPROFILE\aws-oidc-auth\credential-process.exe"
```

2. Create `%USERPROFILE%\aws-oidc-auth\config.json` with your profile (see Configuration below).

3. Add a profile to `%USERPROFILE%\.aws\config` that points to the binary:

```ini
[profile bedrock]
credential_process = C:\Users\you\aws-oidc-auth\credential-process.exe --profile default
region = us-west-2
```

> **Note:** Use the full path with backslashes and include the `.exe` extension. Forward slashes also work in AWS config files on Windows.

---

That's it. Any tool that reads AWS config will now call the binary on demand — `aws`, `boto3`, the Go SDK, LiteLLM, etc.

## Configuration

The binary looks for `config.json` in two places (first match wins):

1. Same directory as the binary
2. `~/aws-oidc-auth/config.json`

---

## Identity Provider Setup

### Okta

Create a **Native** or **SPA** application in Okta with authorization code + PKCE enabled.

**Okta admin console setup:**
1. Applications → Create App Integration → OIDC, Native Application (or SPA).
2. Grant type: Authorization Code.
3. Sign-in redirect URI: `http://localhost:8400/callback`
4. Assignments: assign to the users/groups that need AWS access.
5. Note the **Client ID** and your Okta domain (e.g. `dev-12345.okta.com`).

**config.json:**

```json
{
  "profiles": {
    "default": {
      "provider_domain": "dev-12345.okta.com",
      "client_id": "0oaXXXXXXXXXXXXXXXXX",
      "provider_type": "okta",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/OktaFederatedRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

If using Okta with a Cognito Identity Pool instead of direct STS:

```json
{
  "profiles": {
    "default": {
      "provider_domain": "dev-12345.okta.com",
      "client_id": "0oaXXXXXXXXXXXXXXXXX",
      "provider_type": "okta",
      "federation_type": "cognito",
      "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

**AWS-side IAM trust policy (direct STS):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/dev-12345.okta.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "dev-12345.okta.com:aud": "0oaXXXXXXXXXXXXXXXXX" }
    }
  }]
}
```

---

### Microsoft Entra ID (Azure AD)

The helper supports three Azure authentication modes: **public client** (default), **client secret**, and **certificate**.

**Entra ID app registration setup:**
1. Azure Portal → App registrations → New registration.
2. Redirect URI: **Mobile and desktop applications** → `http://localhost:8400/callback`
3. Under Authentication: enable "Allow public client flows" (for public mode) OR create a client secret/upload a certificate (for confidential modes).
4. Under Token configuration: add optional claims for `email`, `preferred_username` if needed.
5. Note the **Application (client) ID** and **Directory (tenant) ID**.

Your `provider_domain` is: `login.microsoftonline.com/TENANT-ID/v2.0`

#### Public client (simplest)

```json
{
  "profiles": {
    "default": {
      "provider_domain": "login.microsoftonline.com/YOUR-TENANT-ID/v2.0",
      "client_id": "your-application-client-id",
      "provider_type": "azure",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/AzureFederatedRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

#### Client secret (confidential)

Store the secret securely in the OS keyring:

```bash
~/aws-oidc-auth/credential-process --set-client-secret --profile default
# Enter the secret at the prompt (or set AWS_OIDC_AUTH_CLIENT_SECRET env var)
```

```json
{
  "profiles": {
    "default": {
      "provider_domain": "login.microsoftonline.com/YOUR-TENANT-ID/v2.0",
      "client_id": "your-application-client-id",
      "provider_type": "azure",
      "azure_auth_mode": "secret",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/AzureFederatedRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

#### Certificate (confidential)

Generate or obtain a PEM certificate/key pair and upload the public cert to the app registration.

```json
{
  "profiles": {
    "default": {
      "provider_domain": "login.microsoftonline.com/YOUR-TENANT-ID/v2.0",
      "client_id": "your-application-client-id",
      "provider_type": "azure",
      "azure_auth_mode": "certificate",
      "client_certificate_path": "/path/to/cert.pem",
      "client_certificate_key_path": "/path/to/key.pem",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/AzureFederatedRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

On Windows, use forward slashes or escaped backslashes in JSON paths:

```json
"client_certificate_path": "C:/Users/you/certs/cert.pem",
"client_certificate_key_path": "C:/Users/you/certs/key.pem"
```

The certificate paths can also be set via environment variables `AZURE_CLIENT_CERTIFICATE_PATH` and `AZURE_CLIENT_CERTIFICATE_KEY_PATH`.

**AWS-side IAM trust policy (direct STS):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/login.microsoftonline.com/YOUR-TENANT-ID/v2.0" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "login.microsoftonline.com/YOUR-TENANT-ID/v2.0:aud": "your-application-client-id" }
    }
  }]
}
```

---

### Auth0

Create a **Native** application in Auth0 with authorization code + PKCE.

**Auth0 dashboard setup:**
1. Applications → Create Application → Native.
2. Allowed Callback URLs: `http://localhost:8400/callback`
3. Under Advanced Settings → Grant Types: ensure "Authorization Code" is checked.
4. Note the **Client ID** and **Domain** (e.g. `your-tenant.auth0.com`).

**config.json:**

```json
{
  "profiles": {
    "default": {
      "provider_domain": "your-tenant.auth0.com",
      "client_id": "your-auth0-client-id",
      "provider_type": "auth0",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/Auth0FederatedRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

**AWS-side IAM trust policy (direct STS):**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/your-tenant.auth0.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "your-tenant.auth0.com:aud": "your-auth0-client-id" }
    }
  }]
}
```

---

### AWS Cognito User Pool

Use this when a Cognito User Pool is both the identity provider AND the token issuer (common when Cognito is the primary user directory or aggregates upstream IdPs).

**Cognito setup:**
1. Create or use an existing User Pool.
2. App integration → Create app client. Ensure "Authorization code grant" is enabled.
3. Allowed callback URLs: `http://localhost:8400/callback`
4. Note the **App client ID** and the User Pool's **domain** (either a Cognito-hosted domain like `your-pool.auth.us-east-1.amazoncognito.com` or a custom domain).

**config.json:**

```json
{
  "profiles": {
    "default": {
      "provider_domain": "your-pool.auth.us-east-1.amazoncognito.com",
      "client_id": "your-user-pool-client-id",
      "provider_type": "cognito",
      "federation_type": "cognito",
      "identity_pool_id": "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

For direct STS federation with a Cognito User Pool token:

```json
{
  "profiles": {
    "default": {
      "provider_domain": "cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
      "client_id": "your-user-pool-client-id",
      "provider_type": "cognito",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::123456789012:role/CognitoDirectRole",
      "aws_region": "us-east-1",
      "credential_storage": "session"
    }
  }
}
```

---

### AWS SSO / Identity Center

No external IdP configuration needed — this uses the AWS-native device authorization flow.

**Prerequisites:**
- An AWS IAM Identity Center instance with a start URL.
- A permission set assigned to the user.

**config.json:**

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

On first use the binary opens a browser for device authorization. The SSO token is cached in `~/.aws/sso/cache/` (compatible with the AWS CLI cache format).

---

### Multiple profiles

Define multiple profiles in the same config and select with `--profile`:

```json
{
  "profiles": {
    "dev": {
      "federation_type": "sso",
      "sso_start_url": "https://d-xxxxxxxxxx.awsapps.com/start",
      "sso_region": "us-east-1",
      "sso_account_id": "111111111111",
      "sso_role_name": "DeveloperAccess",
      "aws_region": "us-west-2"
    },
    "prod": {
      "provider_domain": "login.microsoftonline.com/TENANT-ID/v2.0",
      "client_id": "your-client-id",
      "provider_type": "azure",
      "federation_type": "direct",
      "federated_role_arn": "arn:aws:iam::222222222222:role/ProdRole",
      "aws_region": "us-east-1"
    }
  }
}
```

```ini
[profile dev]
credential_process = ~/aws-oidc-auth/credential-process --profile dev
region = us-west-2

[profile prod]
credential_process = ~/aws-oidc-auth/credential-process --profile prod
region = us-east-1
```

## Configuration reference

| Field | Description | Default |
|---|---|---|
| `federation_type` | `sso`, `direct`, or `cognito`. Auto-detected from other fields if omitted. | auto |
| `provider_domain` | OIDC issuer domain (not needed for SSO). | — |
| `client_id` | OAuth2 client ID (not needed for SSO). | — |
| `provider_type` | `okta`, `auth0`, `azure`, `cognito`, or `auto` (detected from domain). | `auto` |
| `aws_region` | AWS region for API calls. | `us-east-1` |
| `credential_storage` | `session` (file at `~/.aws/credentials`) or `keyring` (OS secure storage). | `session` |
| `max_session_duration` | STS session duration in seconds. | 43200 (direct) / 28800 (cognito) |
| `sso_start_url` | Identity Center start URL. | — |
| `sso_region` | SSO endpoint region. | value of `aws_region` |
| `sso_account_id` | AWS account ID for SSO role. | — |
| `sso_role_name` | SSO permission set / role name. | — |
| `federated_role_arn` | IAM role ARN for direct STS federation. | — |
| `identity_pool_id` | Cognito Identity Pool ID. | — |
| `azure_auth_mode` | `certificate`, `secret`, or omit for public client. | — |
| `client_certificate_path` | PEM cert path (Azure certificate mode). | — |
| `client_certificate_key_path` | PEM key path (Azure certificate mode). | — |

## Usage

The binary is normally invoked automatically by AWS SDKs via `credential_process`. You can also run it directly.

### macOS / Linux

```bash
# Get credentials (JSON output)
~/aws-oidc-auth/credential-process --profile default

# Check if cached credentials are still valid (exit 0 = valid, 1 = expired)
~/aws-oidc-auth/credential-process --check-expiration --profile default

# Refresh credentials only if expired (useful in cron/launchd)
~/aws-oidc-auth/credential-process --refresh-if-needed --profile default

# Clear cached credentials and force re-authentication
~/aws-oidc-auth/credential-process --clear-cache --profile default

# Store an Azure AD client secret in OS keyring
~/aws-oidc-auth/credential-process --set-client-secret --profile default

# Debug output (to stderr)
AWS_OIDC_AUTH_DEBUG=1 ~/aws-oidc-auth/credential-process --profile default
```

### Windows (PowerShell)

```powershell
# Get credentials (JSON output)
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --profile default

# Check if cached credentials are still valid
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --check-expiration --profile default

# Refresh credentials only if expired (useful in Task Scheduler)
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --refresh-if-needed --profile default

# Clear cached credentials and force re-authentication
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --clear-cache --profile default

# Store an Azure AD client secret in Windows Credential Manager
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --set-client-secret --profile default

# Debug output (to stderr)
$env:AWS_OIDC_AUTH_DEBUG="1"
& "$env:USERPROFILE\aws-oidc-auth\credential-process.exe" --profile default
```

## Environment variables

| Variable | Description |
|---|---|
| `AWS_OIDC_AUTH_PROFILE` | Override the default profile name (alternative to `--profile`). |
| `AWS_OIDC_AUTH_DEBUG` | Set to `1` for verbose debug output on stderr. |
| `AWS_OIDC_AUTH_CLIENT_SECRET` | Provide Azure AD client secret via environment instead of keyring. |

## How it works

1. The binary is invoked (by an SDK or manually).
2. It checks for cached credentials — if valid, returns them immediately.
3. If expired, it attempts a silent refresh using a cached ID token.
4. If no cached token is available:
   - **SSO mode**: runs a device authorization flow (browser opens to Identity Center).
   - **OIDC mode**: runs an authorization code flow with PKCE on `localhost:8400`.
5. The resulting token is exchanged for AWS credentials via STS or Cognito.
6. Credentials are cached (file or keyring) and returned as JSON.

Concurrent invocations are coordinated via port-based locking — only one browser auth flow runs at a time; other callers wait and read the cached result.

## Credential storage modes

**`session`** (default) — writes to `~/.aws/credentials` (or `%USERPROFILE%\.aws\credentials` on Windows) under the profile name. Works everywhere, survives reboots, and is compatible with tools that read the credentials file directly.

**`keyring`** — uses the OS secure storage:

| Platform | Backend | Notes |
|---|---|---|
| macOS | Keychain (`login` keychain) | Prompt-free after first approval |
| Windows | Credential Manager | Credentials split across entries due to 2560-byte value limit |
| Linux | Secret Service (GNOME Keyring / KDE Wallet) | Requires an unlocked session keyring |

The keyring mode is more secure (credentials aren't stored as plaintext on disk) but requires a desktop session. Use `session` mode for headless environments, CI, or Task Scheduler / cron / launchd jobs.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "config.json not found" | Place config.json next to the binary or at `~/aws-oidc-auth/config.json` (`%USERPROFILE%\aws-oidc-auth\config.json` on Windows). |
| "profile X not found" | Check the profile name matches a key in `config.json`'s `"profiles"` object. |
| Browser doesn't open | Copy the URL from stderr and open manually. |
| Port 8400 in use | Another auth flow is in progress — wait for it or kill the process using port 8400. |
| "AssumeRoleWithWebIdentity failed" | Check IAM role trust policy allows the OIDC provider and the token's `sub`/`aud` claims. |
| Credentials expire immediately | Verify your role's max session duration matches `max_session_duration` in config. |
| Windows: "Access denied" on keyring | Run from an interactive desktop session; Windows Credential Manager isn't available in non-interactive service contexts. Use `credential_storage: "session"` for scheduled tasks. |
| Windows: credential_process not found | Use the full absolute path with `.exe` extension in `~/.aws/config`. Backslashes and forward slashes both work. |
| Windows Defender SmartScreen warning | The binary is unsigned. Right-click → Properties → Unblock, or pass through your organization's code-signing process. |

## Platform notes

### Windows-specific behavior

- **Credential Manager size limit**: Windows Credential Manager enforces a ~2560 byte per-entry limit. The helper automatically splits session tokens across multiple entries (`<profile>-keys`, `<profile>-token1`, `<profile>-token2`, `<profile>-meta`) when using `keyring` storage. This is transparent — no user action needed.
- **Paths**: The binary resolves `%USERPROFILE%` for the home directory. Both `C:\Users\you\aws-oidc-auth\config.json` and placing `config.json` next to the `.exe` work.
- **Task Scheduler**: For background refresh (`--refresh-if-needed`), create a scheduled task that runs every 30–60 minutes. Use `credential_storage: "session"` since the keyring isn't available in non-interactive sessions.
- **Firewall**: The OIDC callback listens on `localhost:8400`. Windows Firewall may prompt on first use — the listener only accepts loopback connections.

### macOS-specific behavior

- **Keychain**: On first use with `keyring` storage, macOS prompts to allow keychain access. Click "Always Allow" to avoid repeated prompts.
- **launchd**: For background refresh, create a launchd plist that runs `--refresh-if-needed` periodically. Use `credential_storage: "session"` to avoid keychain unlock prompts in the background.

### Linux-specific behavior

- **Secret Service**: Requires `gnome-keyring` or `kwallet` running with an unlocked session. On headless servers, use `credential_storage: "session"`.
- **Headless/SSH**: The browser-based flows require a display. Use `--refresh-if-needed` from a session where you've previously authenticated, or use SSO mode which can display a URL for you to visit from another device.
