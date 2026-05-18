# otel-helper

Extracts user identity attributes from OIDC JWT tokens and formats them as HTTP headers for OpenTelemetry exporters.

Works alongside the `aws-oidc-auth` credential-process binary but is a separate, independent module.

## How it works

1. Checks for cached headers in `~/.aws-oidc-session/`
2. Falls back to `AWS_OIDC_AUTH_MONITORING_TOKEN` env var
3. Falls back to calling `~/aws-oidc-auth/credential-process --get-monitoring-token`
4. Decodes the JWT and extracts user attributes (email, department, team, etc.)
5. Outputs JSON map of HTTP headers to stdout

## Build

```bash
make macos-arm64    # Apple Silicon
make macos-intel    # Intel Mac
make linux-x64      # Linux AMD64
make linux-arm64    # Linux ARM64
make windows        # Windows AMD64
```

## Usage

```bash
# Normal mode (outputs JSON headers to stdout)
otel-helper

# Test mode (verbose, shows all extracted attributes)
otel-helper --test

# Version
otel-helper --version
```

## Output Headers

| Header | Source |
|--------|--------|
| `x-user-email` | email / preferred_username / mail claim |
| `x-user-id` | SHA256 hash of sub claim (UUID format) |
| `x-user-name` | cognito:username / preferred_username |
| `x-organization` | Detected from issuer domain |
| `x-department` | department / dept / division claim |
| `x-team-id` | team / team_id / group claim |
| `x-cost-center` | cost_center / costCenter claim |
| `x-manager` | manager / manager_email claim |
| `x-location` | location / office_location claim |
| `x-role` | role / job_title / title claim |

## Tests

```bash
make test
```
