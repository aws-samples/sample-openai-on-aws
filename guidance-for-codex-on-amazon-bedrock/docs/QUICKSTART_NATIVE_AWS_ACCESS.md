# Quick Start: Native AWS Access

Deploy Codex on Bedrock with IAM Identity Center authentication in 5-60 minutes using direct CloudFormation deployment.

**Use this pattern if:**
- You already use AWS IAM Identity Center, OR
- You're willing to set up IdC + SAML federation, AND
- Soft monitoring (alerts, not blocking) is sufficient

---

## Overview

**What You're Deploying:**
```
Corporate IdP (Okta/Azure) -> SAML -> IAM Identity Center -> AWS credentials -> Bedrock
```

---

## Prerequisites

### Required

- [ ] AWS account with admin permissions (IAM, CloudFormation, Identity Center)
- [ ] Amazon Bedrock activated in target region (e.g., `us-west-2`)
- [ ] AWS CLI v2 installed ([download](https://aws.amazon.com/cli/))
- [ ] Identity provider with SAML 2.0 support (Okta, Azure AD, Auth0, Google Workspace)
- [ ] [Codex CLI](https://developers.openai.com/codex/cli) installed locally

### IdP-Specific Guides

For identity provider setup with IAM Identity Center, see AWS documentation:
- [Okta](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-okta.html)
- [EntraID](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-entra.html)
- [Auth0, Google Workspace, and others](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-identity-source-idp.html)

---

## Deployment Paths

### Path A: IdC Already Configured

**If your organization already uses IAM Identity Center for AWS access:**

#### Step 1: Clone Repository

```bash
git clone https://github.com/aws-samples/sample-openai-on-aws.git
cd sample-openai-on-aws/guidance-for-codex-on-amazon-bedrock
```

#### Step 2: Deploy the Bedrock Auth Stack

```bash
# Set deployment variables
AWS_REGION=us-west-2                          # Bedrock region
STACK_NAME=codex-bedrock-idc
TEMPLATE_FILE=deployment/infrastructure/bedrock-auth-idc.yaml

# Deploy CloudFormation stack
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      RoleName=CodexBedrockIdCRole \
      PolicyName=CodexBedrockInvokePolicy \
      PermissionSetNamePattern='CodexBedrockUser_*' \
      AllowedBedrockRegions='us-east-1,us-west-2' \
      AllowedModelIdPattern='*' \
      MaxSessionDurationSeconds=28800

# Wait for completion (2-3 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"

# Read the outputs (capture RoleArn and PolicyArn)
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs'
```

**Stack creates:**
- IAM Role: `CodexBedrockIdCRole`
- IAM Managed Policy: `CodexBedrockInvokePolicy` (scoped to `bedrock:InvokeModel*` and `bedrock-mantle:CreateInference` for GPT-5.4 via the Mantle endpoint)
- Trust relationship: trusted by `AWSReservedSSO_CodexBedrockUser_*` role-chaining

#### Step 3: Create the Permission Set in IAM Identity Center

The CloudFormation stack provisions IAM resources but cannot create the permission set itself — IAM Identity Center lives outside CloudFormation's scope. Use the CLI steps below (recommended for automation) or the console fallback.

**Option A: CLI (scriptable, CI/CD friendly)**

```bash
# Get your IdC instance ARN
IDC_INSTANCE_ARN=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].InstanceArn' --output text)
IDENTITY_STORE_ID=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].IdentityStoreId' --output text)

# Read the policy ARN from Step 2 outputs
POLICY_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`PolicyArn`].OutputValue' --output text)

# Create the permission set
PS_ARN=$(aws sso-admin create-permission-set \
  --instance-arn "$IDC_INSTANCE_ARN" \
  --name CodexBedrockUser \
  --session-duration PT8H \
  --region us-east-1 \
  --query 'PermissionSet.PermissionSetArn' --output text)

# Attach the customer-managed policy
aws sso-admin attach-customer-managed-policy-reference-to-permission-set \
  --instance-arn "$IDC_INSTANCE_ARN" \
  --permission-set-arn "$PS_ARN" \
  --customer-managed-policy-reference "Name=CodexBedrockInvokePolicy,Path=/" \
  --region us-east-1

# Assign to a group (recommended) or individual user
# For a group:
GROUP_ID=$(aws identitystore list-groups \
  --identity-store-id "$IDENTITY_STORE_ID" \
  --filters AttributePath=DisplayName,AttributeValue=<YourCodexGroup> \
  --region us-east-1 \
  --query 'Groups[0].GroupId' --output text)

# Resolve the current account ID (used as the assignment target)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws sso-admin create-account-assignment \
  --instance-arn "$IDC_INSTANCE_ARN" \
  --permission-set-arn "$PS_ARN" \
  --principal-type GROUP --principal-id "$GROUP_ID" \
  --target-type AWS_ACCOUNT --target-id "$AWS_ACCOUNT_ID" \
  --region us-east-1

# Wait for assignment to complete (~15 seconds)
sleep 15
```

**Option B: AWS Console**

1. Open IAM Identity Center: https://console.aws.amazon.com/singlesignon
2. Navigate to **Multi-account permissions** -> **Permission sets**
3. Click **Create permission set** -> **Custom permission set**
4. Name: `CodexBedrockUser`, session duration: `8 hours`
5. Under **Customer managed policies**, attach the policy ARN from Step 2 outputs
6. Navigate to **AWS accounts** -> select your account -> **Assign users or groups**
7. Select permission set `CodexBedrockUser`, select your Codex developer group, click **Submit**

#### Step 4: Distribute Configuration to Developers

Share three values with your developers:

1. **IdC Start URL** - From IdC console (e.g., `https://d-xxxxxxxxxx.awsapps.com/start`)
2. **AWS Account ID** - Your 12-digit account ID
3. **Permission Set Name** - The role name, e.g., `CodexBedrockUser`

Developers will add these to their `~/.aws/config` and `~/.codex/config.toml` files. See [Developer Configuration](#developer-configuration) below for the exact config snippets.

**Distribution options:**
- Email/Slack the three values + config snippets from the [Developer Configuration](#developer-configuration) section
- Add to your internal wiki/docs portal
- Use your existing onboarding automation (e.g., internal CLI tool, Terraform workspaces)

---

### Path B: IdC Not Configured (30-60 minutes)

**If you need to set up IAM Identity Center from scratch:**

#### Step 1: Enable IAM Identity Center

```bash
# 1. Choose your IdC home region (this is where IdC lives; can be
#    different from Bedrock region)
AWS_REGION=us-east-1

# 2. Enable Identity Center via the AWS Console:
#    https://console.aws.amazon.com/singlesignon
#    Click "Enable"
#
#    This creates your IdC instance and gives you:
#    - Start URL: https://d-xxxxxxxxxx.awsapps.com/start
#    - Identity source: (default) Identity Center directory
```

#### Step 2: Connect Your IdP via SAML

**Option A: External IdP (Okta, Azure AD, Auth0)**

Follow AWS IdC setup guides for your identity provider:
- [Okta](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-okta.html)
- [EntraID](https://docs.aws.amazon.com/singlesignon/latest/userguide/gs-entra.html)
- [Auth0 and others](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-identity-source-idp.html)

**Option B: Identity Center Directory (Built-in)**

If you don't have an external IdP:

1. In IdC console, go to **Settings** -> **Identity source**
2. Default: **Identity Center directory** (AWS-managed user directory)
3. Click **Users** -> **Add user**
4. Create test user for validation
5. Click **Groups** -> **Create group**
6. Name: `Codex-Developers`
7. Add users to group

#### Step 3: Deploy the Bedrock Auth Stack

Follow [Path A, Step 2](#step-2-deploy-the-bedrock-auth-stack) above.

#### Step 4: Create the Permission Set

Follow [Path A, Step 3](#step-3-create-the-permission-set-in-iam-identity-center) above.

#### Step 5: Distribute Configuration

Follow [Path A, Step 4](#step-4-distribute-configuration-to-developers) above.

---

## Developer Configuration

Each developer needs two configuration snippets: an AWS CLI profile that uses SSO, and a Codex `config.toml` that points at Amazon Bedrock.

### AWS CLI Profile (`~/.aws/config`)

Append the following block to `~/.aws/config`. Replace placeholder values from the admin's distribution.

```ini
[sso-session codex-bedrock-sso]
sso_start_url = https://d-xxxxxxxxxx.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access

[profile codex-bedrock]
sso_session = codex-bedrock-sso
sso_account_id = 123456789012
sso_role_name = CodexBedrockUser
region = us-west-2
```

### Codex Configuration (`~/.codex/config.toml`)

Append the following block to the user-level `~/.codex/config.toml`. Codex
ignores provider settings in project-local `.codex/config.toml` files. The
Bedrock provider uses the AWS SDK credential chain, so the `profile` value
must match the `[profile ...]` name in `~/.aws/config`.

```toml
model_provider = "amazon-bedrock"
model = "openai.gpt-5.4"

[model_providers.amazon-bedrock.aws]
region = "us-west-2"
profile = "codex-bedrock"
```

This guide keeps `openai.gpt-5.4` in the sample because the walkthrough uses
`us-west-2`. OpenAI recommends the latest GPT-5 family model for Codex, so if
you deploy in `us-east-2`, switch the snippet to `model = "openai.gpt-5.5"`
and update the Bedrock region to match.

For advanced Codex configuration options (model parameters, sandbox modes, custom providers), see the [OpenAI Codex configuration reference](https://developers.openai.com/codex/config-advanced).

For enterprise rollout controls and Codex repo customization, use the official
OpenAI documentation:
- [Managed configuration (`requirements.toml`)](https://developers.openai.com/codex/enterprise/managed-configuration#admin-enforced-requirements-requirementstoml)
- [Sandbox and approvals](https://developers.openai.com/codex/concepts/sandboxing#configure-defaults)
- [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [Customization](https://developers.openai.com/codex/concepts/customization#next-step)

### Authenticate and Launch

```bash
# 1. Sign in via Identity Center (browser opens)
aws sso login --profile codex-bedrock

# 2. Verify access
aws sts get-caller-identity --profile codex-bedrock

# Expected output:
# {
#   "UserId": "AROA...:user@company.com",
#   "Account": "123456789012",
#   "Arn": "arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_CodexBedrockUser_.../user@company.com"
# }

# 3. Launch Codex
codex
```

Codex reads `~/.codex/config.toml`, picks up the `amazon-bedrock` provider, and uses the AWS SDK to load credentials from the `codex-bedrock` profile. When the SSO token expires, `aws sso login` refreshes it.

---

## Validation

### Test Authentication

```bash
# 1. Refresh SSO token
aws sso login --profile codex-bedrock

# 2. Inspect temporary credentials (optional)
aws configure export-credentials --profile codex-bedrock --format process | jq

# Expected output (truncated):
# {
#   "Version": 1,
#   "AccessKeyId": "ASIA...",
#   "SecretAccessKey": "...",
#   "SessionToken": "...",
#   "Expiration": "2026-05-30T18:30:00Z"
# }

# 3. Test Bedrock access directly (uses gpt-oss-20b via standard InvokeModel to confirm IAM is wired up)
aws bedrock-runtime invoke-model \
  --model-id openai.gpt-oss-20b-1:0 \
  --cli-binary-format raw-in-base64-out \
  --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}' \
  --region us-west-2 \
  --profile codex-bedrock \
  output.json

cat output.json | jq
```

### Test Codex Integration

```bash
# 1. Confirm the Codex config block is present
grep -A6 "model_provider" ~/.codex/config.toml

# Expected:
# model_provider = "amazon-bedrock"
# model = "openai.gpt-5.4"
# 
# [model_providers.amazon-bedrock.aws]
# region = "us-west-2"
# profile = "codex-bedrock"

# 2. Run a Codex test prompt
codex exec --skip-git-repo-check --sandbox read-only "Write a hello world function in Python"

# Expected: Codex generates Python code using Bedrock
# Note: gpt-oss models emit a reasoning trace before the answer — this is expected.
```

---

## Optional: Add Monitoring (OTel)

**If you want CloudWatch dashboards for usage tracking:**

### Step 1: Deploy the Networking Stack

```bash
AWS_REGION=us-west-2
NETWORKING_STACK=codex-networking

aws cloudformation deploy \
  --stack-name "$NETWORKING_STACK" \
  --template-file deployment/infrastructure/networking.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      VpcCidr=10.0.0.0/16
```

### Step 2: Deploy the OTel Collector Stack

```bash
OTEL_STACK=codex-otel-collector

# Pull VPC and subnet IDs from networking stack
VPC_ID=$(aws cloudformation describe-stacks \
  --stack-name "$NETWORKING_STACK" --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' --output text)

SUBNET_IDS=$(aws cloudformation describe-stacks \
  --stack-name "$NETWORKING_STACK" --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`SubnetIds`].OutputValue' --output text)

aws cloudformation deploy \
  --stack-name "$OTEL_STACK" \
  --template-file deployment/infrastructure/otel-collector.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      VpcId="$VPC_ID" \
      SubnetIds="$SUBNET_IDS" \
      CustomDomainName=otel.codex.example.com \
      HostedZoneId=Z0123456789ABCDEFGHIJ

# Capture the collector ALB URL
COLLECTOR_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$OTEL_STACK" --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`CollectorEndpoint`].OutputValue' --output text)
echo "$COLLECTOR_ENDPOINT"
```

### Step 3: Add the OTel Block to `~/.codex/config.toml`

Append the following block. Substitute the collector endpoint captured above.

```toml
[otel.exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/logs"
protocol = "binary"

[otel.metrics_exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/metrics"
protocol = "binary"

[otel.trace_exporter.otlp-http]
endpoint = "https://otel.codex.example.com/v1/traces"
protocol = "binary"
```

Codex automatically exports metrics to the central collector, which forwards them to CloudWatch under the `Codex` namespace. View the dashboard under **CloudWatch -> Dashboards -> CodexOnBedrock** (deployed by the `codex-otel-dashboard` stack).

---

## Troubleshooting

### Issue: `aws sso login` fails with "Invalid start URL"

**Cause:** IdC start URL is incorrect or region mismatch

**Fix:**
```bash
# Verify IdC configuration
aws sso list-instances --region us-east-1 | jq

# Check start URL in ~/.aws/config
grep sso_start_url ~/.aws/config
```

### Issue: "AccessDeniedException" when calling Bedrock

**Cause:** Permission set not attached or policy missing `bedrock:InvokeModel`

**Fix:**
1. Verify permission set assignment in IdC console
2. Check policy ARN is attached to permission set
3. Wait 5 minutes for propagation
4. Re-run `aws sso login --profile codex-bedrock`

### Issue: Codex says "No credentials found"

**Cause:** AWS profile is missing or `model_providers.amazon-bedrock.aws.profile` doesn't match

**Fix:**
```bash
# Confirm the profile exists in ~/.aws/config
grep -A4 "profile codex-bedrock" ~/.aws/config

# Confirm the Codex provider points at the same profile
grep -A4 "model_providers.amazon-bedrock.aws" ~/.codex/config.toml
```

### Issue: Browser doesn't open for SSO login

**Cause:** AWS CLI not in PATH or default browser not detected

**Fix:**
```bash
which aws

# Install AWS CLI v2 if missing:
# macOS:    brew install awscli
# Linux:    sudo apt install awscli
# Windows:  winget install Amazon.AWSCLI
```

### More troubleshooting

See [operate-troubleshooting.md](operate-troubleshooting.md)

---

## Cleanup

**To remove the Native AWS Access deployment:**

```bash
# 1. Developers remove their managed config blocks
#    - Delete the codex-bedrock profile and sso-session entry from ~/.aws/config
#    - Delete the model_providers.amazon-bedrock block from ~/.codex/config.toml
#    - rm -rf ~/.aws/sso/cache

# 2. Admin deletes the OTel and dashboard stacks (if deployed)
#    Delete dashboards first (no dependents), then collector, then networking.
#    Wait between dependent stacks — networking delete fails if collector VPC resources still exist.
aws cloudformation delete-stack --stack-name codex-otel-dashboard --region us-west-2
aws cloudformation delete-stack --stack-name codex-dashboard --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name codex-otel-dashboard --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name codex-dashboard --region us-west-2
aws cloudformation delete-stack --stack-name codex-otel-collector --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name codex-otel-collector --region us-west-2
aws cloudformation delete-stack --stack-name codex-networking --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name codex-networking --region us-west-2

# 3. Admin removes the permission set
#    Account assignments must be deleted before the permission set can be removed.
#    Do this BEFORE deleting the auth stack — the stack delete will fail with
#    DELETE_FAILED if the customer-managed policy is still attached to the permission set.
IDC_INSTANCE_ARN=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].InstanceArn' --output text)
IDENTITY_STORE_ID=$(aws sso-admin list-instances --region us-east-1 \
  --query 'Instances[0].IdentityStoreId' --output text)
PS_ARN=$(aws sso-admin list-permission-sets --instance-arn "$IDC_INSTANCE_ARN" --region us-east-1 \
  --query 'PermissionSets[]' --output text | while read arn; do
    name=$(aws sso-admin describe-permission-set --instance-arn "$IDC_INSTANCE_ARN" \
      --permission-set-arn "$arn" --region us-east-1 --query 'PermissionSet.Name' --output text 2>/dev/null)
    [[ "$name" == "CodexBedrockUser" ]] && echo "$arn"
  done)

# Delete account assignments first (one per user/group assigned)
aws sso-admin delete-account-assignment \
  --instance-arn "$IDC_INSTANCE_ARN" \
  --permission-set-arn "$PS_ARN" \
  --target-id <AccountId> --target-type AWS_ACCOUNT \
  --principal-type GROUP --principal-id <GroupId> \
  --region us-east-1
# Wait ~15 seconds for deletion to propagate, then delete the permission set
sleep 15
aws sso-admin delete-permission-set \
  --instance-arn "$IDC_INSTANCE_ARN" \
  --permission-set-arn "$PS_ARN" \
  --region us-east-1

# 4. Admin deletes the Bedrock auth stack
#    Note: the auth stack lives in the Bedrock region (us-west-2, the
#    AWS_REGION used at deploy time), NOT us-east-1. us-east-1 is only the
#    IdC home region used for the sso-admin commands above.
aws cloudformation delete-stack \
  --stack-name codex-bedrock-idc \
  --region us-west-2
aws cloudformation wait stack-delete-complete \
  --stack-name codex-bedrock-idc \
  --region us-west-2
```

---

## Next Steps

- **Add monitoring:** [Optional: Add Monitoring (OTel)](#optional-add-monitoring-otel)
- **Migrate to LLM Gateway:** [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md)
- **Scale to more users:** Distribute configuration via your existing internal docs portal or self-service tooling
- **Monitor costs:** Set up CloudWatch alarms on Bedrock spend

---

## Support

- **Documentation:** [../QUICKSTART.md](../QUICKSTART.md)
- **Issues:** [GitHub Issues](https://github.com/aws-samples/sample-openai-on-aws/issues)
- **Codex configuration reference:** [OpenAI Codex docs](https://developers.openai.com/codex/config-advanced)
- **Technical guide:** [deploy-identity-center.md](deploy-identity-center.md)
