# Deploy — IAM Identity Center (Recommended)

Federate AWS IAM Identity Center (IdC) from your existing corporate IdP so
developers get AWS credentials backed by their SSO identity. Codex reads the
resulting profile through the standard AWS SDK credential chain.

## Prerequisites

- **AWS Organizations** enabled (IdC requires Orgs).
- An IdP that can federate to AWS via SAML 2.0 + SCIM 2.0. Supported: EntraID,
  Okta, Ping, JumpCloud, Google Workspace, CyberArk, OneLogin.
- Admin access in both the AWS management account and the corporate IdP.
- AWS CLI v2 distributable to end users via winget / MSI / Homebrew / MDM.
- Bedrock activated in the target region(s). See [reference-regions.md](reference-regions.md) for how to verify current model availability in AWS.

## Admin setup (one-time)

### 1. Enable IdC in the AWS management account

Pin the IdC instance to a region — it is single-region, though permission sets can
grant access to Bedrock in any region.

### 2. Connect your IdP as the identity source

EntraID and Okta have first-class gallery apps with AWS-published setup guides.
Exchange SAML metadata, then enable SCIM automatic provisioning using the
tenant URL + bearer token IdC generates.

Known SCIM quirks:
- Nested groups from EntraID do **not** flatten — provision leaf groups.
- Attribute mapping for email/username occasionally trips initial setup.

### 3. Deploy the Bedrock auth stack

```bash
aws cloudformation deploy \
  --stack-name codex-bedrock-idc \
  --template-file deployment/infrastructure/bedrock-auth-idc.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

Outputs include the customer-managed policy ARN to attach to the permission
set in the next step.

### 4. Create the `CodexBedrockUser` permission set

Replace `<account-id>` and `<group-id>` with your values. Session duration defaults to
8 hours; raise it up to 12 hours (`PT12H`) for long Codex sessions.

```bash
# Discover your IdC instance ARN and Identity Store ID
IDC_ARN=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].InstanceArn' --output text)
IDENTITY_STORE_ID=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].IdentityStoreId' --output text)

ACCOUNT_ID=123456789012
POLICY_NAME=CodexBedrockInvokePolicy   # matches PolicyName parameter from bedrock-auth-idc.yaml

# Look up your Codex developer group ID
GROUP_ID=$(aws identitystore list-groups \
  --identity-store-id "$IDENTITY_STORE_ID" \
  --filters AttributePath=DisplayName,AttributeValue=<YourCodexGroup> \
  --region us-east-1 \
  --query 'Groups[0].GroupId' --output text)

# Create the permission set
PS_ARN=$(aws sso-admin create-permission-set \
  --instance-arn "$IDC_ARN" \
  --name CodexBedrockUser \
  --session-duration PT8H \
  --region us-east-1 \
  --query 'PermissionSet.PermissionSetArn' --output text)

# Attach the customer-managed policy from step 3
aws sso-admin attach-customer-managed-policy-reference-to-permission-set \
  --instance-arn "$IDC_ARN" \
  --permission-set-arn "$PS_ARN" \
  --customer-managed-policy-reference "Name=$POLICY_NAME,Path=/" \
  --region us-east-1

# Assign the permission set to the Codex user group in the target account
aws sso-admin create-account-assignment \
  --instance-arn "$IDC_ARN" \
  --permission-set-arn "$PS_ARN" \
  --principal-type GROUP --principal-id "$GROUP_ID" \
  --target-type AWS_ACCOUNT --target-id "$ACCOUNT_ID" \
  --region us-east-1

# Wait ~15 seconds for the assignment to propagate before testing credentials
sleep 15
```

Console equivalent: IAM Identity Center → Permission sets → Create, then
attach the customer-managed policy by name and assign to the group in each
target account.

### 5. Distribute the developer configuration

Each developer needs two snippets — an AWS CLI profile that uses SSO, and a
Codex `config.toml` that points at Amazon Bedrock. Share these directly (email,
chat, internal wiki) or package them and upload to S3 with a presigned URL.

**AWS CLI profile** — append to `~/.aws/config`:

```ini
[sso-session codex]
sso_start_url = https://d-xxxxxxxxxx.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access

[profile codex]
sso_session = codex
sso_account_id = 123456789012
sso_role_name = CodexBedrockUser
region = us-west-2
```

**Codex configuration** — append to the user-level `~/.codex/config.toml`:

```toml
model_provider = "amazon-bedrock"
model = "openai.gpt-5.4"

[model_providers.amazon-bedrock]
name = "Amazon Bedrock"

[model_providers.amazon-bedrock.aws]
region = "us-west-2"
profile = "codex"
```

Keep provider settings in user-level `~/.codex/config.toml`; Codex ignores
`model_provider` and `model_providers` in project-local `.codex/config.toml`
files. This sample keeps `openai.gpt-5.4` so the `us-west-2` walkthrough works
end to end. If you standardize on `us-east-2`, prefer `openai.gpt-5.5` to
follow OpenAI's latest-model guidance for Codex.

For advanced Codex configuration (model parameters, sandbox modes, custom
providers), see the
[OpenAI Codex configuration reference](https://developers.openai.com/codex/config-advanced).

**Distribution:** Share the two snippets above via email, Slack, your internal wiki, or existing onboarding automation (MDM, internal CLI tools, etc.). Organizations that need packaged bundles can zip the snippets and distribute via S3 presigned URLs or internal package repositories.

## End-user flow

```bash
# Append the AWS profile snippet to ~/.aws/config and the [model_providers...]
# block to ~/.codex/config.toml as shown above.
aws sso login --profile codex
codex                  # AWS_PROFILE is resolved via the [model_providers.amazon-bedrock.aws] block
```

`aws sso login` opens a browser for IdC sign-in and caches an 8-hour token.
Codex picks up the SSO credentials through the standard AWS SDK credential chain.

### Headless / remote hosts (no local browser)

`aws sso login` defaults to opening a browser on the same machine. On headless
hosts — bastions, EC2 dev boxes, SSH-only field laptops, CI runners — use the
device-code flow instead:

```bash
aws sso login --profile codex --no-browser
# Prints a verification URL + one-time code.
# Open the URL on any device where you can sign in to your IdP,
# enter the code, approve. Back on the headless host, the command
# returns once the cache is populated.
```

Pre-warm the cache with `--no-browser` before starting Codex; re-run when the
8-hour token expires. Fully non-interactive fleet/CI pre-warming is not yet
supported.

### `aws login` (console-login) profiles

Codex ≥ 0.130.0 also resolves credentials from `aws login` console-login
profiles (`login_session`) via the standard AWS SDK credential chain.

### Uninstall

Remove the `[sso-session codex]` and `[profile codex]` blocks from
`~/.aws/config`, then remove the `[model_providers.amazon-bedrock]` block (and
optional `[otel]` block) from `~/.codex/config.toml`. Take a timestamped
backup of each file first. To revoke any cached SSO tokens, run
`aws sso logout --profile codex`.

## Validation

```bash
aws sso login --profile codex
aws sts get-caller-identity --profile codex
# Expect: Arn: arn:aws:sts::<account>:assumed-role/AWSReservedSSO_CodexBedrockUser_.../<sso-user>

aws bedrock-runtime converse \
  --profile codex --region us-west-2 \
  --model-id openai.gpt-oss-120b-1:0 \
  --messages '[{"role":"user","content":[{"text":"OK?"}]}]'
```

If this succeeds, the IdC → Bedrock auth chain is working. The Codex
`amazon-bedrock` provider routes through a mantle endpoint; set the `model`
line in the installed `~/.codex/config.toml` to a mantle-served model to
round-trip from the Codex client — no auth or IAM changes are needed.

## CloudTrail attribution

Every `bedrock:InvokeModel` call produces a CloudTrail event where:

- `userIdentity.type` = `AssumedRole`
- `userIdentity.principalId` = `<role-id>:<SSO-username>`
- `userIdentity.sessionContext.sessionIssuer.userName` = permission-set role name
- Session name carries the corporate UPN (per SCIM attribute mapping)

Pair with Bedrock Application Inference Profiles for per-team cost allocation
in CUR.

## Quota & budgets

IdC provides per-user *attribution*, not enforcement. What you can and cannot
do on this path:

| Want | Available | How |
|---|---|---|
| Per-team quota partitioning | Yes | Bedrock **Application Inference Profiles** — grant different IdC groups access to different profile ARNs via the permission set; each profile carries its own quota. |
| Restrict users to specific models / regions / profiles | Yes | IAM policy conditions in the customer-managed policy attached to the permission set. |
| Alert when a user crosses a usage threshold | Yes | CloudWatch alarm on the OTel `user.id` dimension (requires the optional OTel stack below). Alerts only — no cutoff. |
| Hard per-user token / dollar budget with automatic cutoff | **No** | Not achievable with IdC alone. This is the LiteLLM Gateway's job — see `docs/01-decide.md`. |

Bedrock service quotas themselves are account-level (requests/min, tokens/min
per model); they throttle the whole account, not individual users.

## Optional: OTel usage dashboard

Per-user usage attribution in CloudWatch. The order is: **deploy the collector
stack first**, then add an `[otel]` block to each developer's
`~/.codex/config.toml` pointing at the collector's ALB endpoint and stamping
the developer's SSO identity as the `x-user-id` header. The collector
(`deployment/infrastructure/otel-collector.yaml`) extracts that header into a
CloudWatch `user.id` dimension.

### 1. Deploy the collector stack

```bash
deployment/scripts/deploy-otel-stack.sh \
  --region us-west-2 \
  --custom-domain otel.codex.example.com \
  --hosted-zone-id Z0123456789ABCDEFGHIJ
```

The script deploys three stacks in order (`codex-otel-networking`,
`codex-otel-collector`, `codex-otel-dashboard`) and prints the ALB endpoint.
A full deployment takes approximately 5 minutes in a clean account.

Useful flags:

| Flag | Purpose |
|---|---|
| `--region` | Target region (default `us-west-2`). |
| `--stack-prefix` | Rename the three stacks (default `codex-otel`). |
| `--custom-domain` | Required HTTPS endpoint domain for the collector. |
| `--hosted-zone-id` | Required Route 53 zone ID for certificate DNS validation. |
| `--dashboard-name` | CloudWatch dashboard name (default `CodexOnBedrock`). |
| `--input-price` / `--output-price` / `--cached-input-price` | Per-1M-token USD for the dashboard's spend-estimate widgets. Defaults are placeholders — update after GPT-5.4 pricing publishes. |

### 2. Add JWT validation (optional production hardening)

The collector is HTTPS-only. Without JWT validation it still accepts any
`x-user-id` value (trust-on-distribution). For stronger attribution, pass the
OIDC flags below to enable ALB JWT validation:

```bash
deployment/scripts/deploy-otel-stack.sh \
  --region us-west-2 \
  --custom-domain otel.codex.example.com \
  --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --oidc-issuer https://cognito-idp.us-west-2.amazonaws.com/<pool-id> \
  --oidc-jwks https://cognito-idp.us-west-2.amazonaws.com/<pool-id>/.well-known/jwks.json \
  --oidc-client-id <app-client-id>
```

With JWT validation enabled, each developer also needs a bearer token —
include it as an additional static header alongside `x-user-id` in the
`[otel.headers]` block shown below. Per-user token distribution is out of
scope for this document.

**Trade-offs:** HTTPS without JWT is simpler but accepts any `x-user-id` value. JWT validation verifies tokens but requires OIDC issuer configuration and developer token distribution.

### 3. Add the OTel block to the developer config

Append an `[otel]` block to each developer's `~/.codex/config.toml` pointing at
the collector ALB endpoint printed in step 1. Stamp the developer's SSO
identity into the `x-user-id` header so every metric carries that dimension:

```toml
[otel.exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/logs"
protocol = "binary"
[otel.exporter.otlp-http.headers]
x-user-id = "user@company.com"   # developer's SSO identity — used for per-user attribution in CloudWatch

[otel.metrics_exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/metrics"
protocol = "binary"
[otel.metrics_exporter.otlp-http.headers]
x-user-id = "user@company.com"

[otel.trace_exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/traces"
protocol = "binary"
[otel.trace_exporter.otlp-http.headers]
x-user-id = "user@company.com"
```

Resolve the SSO identity for a logged-in profile with
`aws sts get-caller-identity --profile codex --query Arn` (the SSO username
follows the final `/` of the assumed-role ARN).

## Known pitfalls

- **Session duration.** The 8-hour default can interrupt long Codex runs; raise it up to
  12 hours on the permission set, or accept `aws sso login` re-authentication as UX.
- **GovCloud.** IdC works in GovCloud but must be enabled separately; FedRAMP
  parity is an open question.
- **Single-region IdC.** The control plane is regional; Bedrock calls can target
  any region the permission set allows.

## Teardown

```bash
# Remove the account assignment and permission set via IdC console or CLI
aws sso-admin delete-account-assignment ...
aws sso-admin delete-permission-set ...

# Remove the stack
aws cloudformation delete-stack \
  --stack-name codex-bedrock-idc --region us-west-2
```

## References

- [IdC with EntraID setup guide](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-entra.html)
- [IdC with Okta setup guide](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-okta.html)
- [IdC SCIM automatic provisioning](https://docs.aws.amazon.com/singlesignon/latest/userguide/provision-automatically.html)
- [SSO session duration](https://docs.aws.amazon.com/singlesignon/latest/userguide/howtosessionduration.html)
- [AWS CLI SSO profile configuration](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html)
