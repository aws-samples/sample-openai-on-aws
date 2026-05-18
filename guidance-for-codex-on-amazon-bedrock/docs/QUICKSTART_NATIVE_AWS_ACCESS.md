# Quick Start: Native AWS Access

Deploy Codex on Bedrock with IAM Identity Center authentication in 5-60 minutes.

**Use this pattern if:**
- ✅ You already use AWS IAM Identity Center, OR
- ✅ You're willing to set up IdC + SAML federation, AND
- ✅ Soft monitoring (alerts, not blocking) is sufficient

---

## Overview

**What You're Deploying:**
```
Corporate IdP (Okta/Azure) → SAML → IAM Identity Center → AWS credentials → Bedrock
```

---

## Prerequisites

### Required

- [ ] AWS account with admin permissions (IAM, CloudFormation, Identity Center)
- [ ] Amazon Bedrock activated in target region (e.g., `us-west-2`)
- [ ] AWS CLI v2 installed ([download](https://aws.amazon.com/cli/))
- [ ] Python 3.10-3.13 + uv ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- [ ] Identity provider with SAML 2.0 support (Okta, Azure AD, Auth0, Google Workspace)

### IdP-Specific Guides

Choose your identity provider:
- **Okta** → [providers/okta-setup.md](providers/okta-setup.md) *(coming soon)*
- **Microsoft Entra ID (Azure AD)** → [providers/microsoft-entra-id-setup.md](providers/microsoft-entra-id-setup.md) *(coming soon)*
- **Auth0** → [providers/auth0-setup.md](providers/auth0-setup.md) *(coming soon)*
- **Google Workspace** → [providers/google-workspace-setup.md](providers/google-workspace-setup.md) *(coming soon)*

---

## Deployment Paths

### Path A: IdC Already Configured

**If your organization already uses IAM Identity Center for AWS access:**

```bash
# 1. Clone repo
git clone https://github.com/aws-samples/guidance-for-codex-on-aws.git
cd guidance-for-codex-on-aws/guidance-for-codex-on-amazon-bedrock

# 2. Install CLI
cd source/
uv sync

# 3. Run wizard (select "IAM Identity Center" path)
uv run cxwb init

# Answer prompts:
# - Deployment path? → IAM Identity Center
# - Manage infrastructure? → Yes (deploy new stacks)
# - IdC start URL? → https://d-xxxxxxxxxx.awsapps.com/start
# - IdC region? → (your IdC home region, e.g., us-east-1)
# - AWS account ID? → 123456789012
# - Permission set name? → CodexBedrockUser
# - Bedrock region? → us-west-2
# - Default model? → openai.gpt-5.4
# - Profile name? → codex-bedrock

# 4. Deploy CloudFormation stack
uv run cxwb deploy --profile codex-bedrock

# This creates:
# - IAM role: BedrockInvokeRole
# - IAM policy: CodexBedrockPolicy (scoped to bedrock:InvokeModel)
# Output: Customer-managed policy ARN

# 5. Create permission set in IAM Identity Center
# (One-time manual step via AWS Console)
```

**AWS Console Steps (Identity Center):**

1. Open IAM Identity Center: https://console.aws.amazon.com/singlesignon
2. Navigate to **Multi-account permissions** → **Permission sets**
3. Click **Create permission set**
4. Choose **Custom permission set**
5. Name: `CodexBedrockUser`
6. Session duration: `8 hours` (or your org policy)
7. Under **Customer managed policies**, attach the policy ARN from step 4
8. Click **Create**
9. Navigate to **AWS accounts** → Select your account → **Assign users or groups**
10. Select permission set: `CodexBedrockUser`
11. Select users/groups: Your Codex developer group
12. Click **Submit**

```bash
# 6. Generate developer bundle
uv run cxwb distribute --profile codex-bedrock --bucket my-distribution-bucket

# Output: S3 presigned URL valid for 7 days
# Share this URL with developers
```

**Bundle contents:**
```
<profile-name>-config/
├── install.sh              # Developer runs this
├── uninstall.sh            # Cleanup script
├── codex-sso-creds         # Credential helper (bash script)
├── aws-config.snippet      # AWS config fragment
├── codex-config.toml.snippet # Codex config fragment
└── DEV-SETUP.md            # Developer instructions
```

---

### Path B: IdC Not Configured (30-60 minutes)

**If you need to set up IAM Identity Center from scratch:**

#### Step 1: Enable IAM Identity Center

```bash
# 1. Choose your IdC home region
# (This is where IdC lives; can be different from Bedrock region)
AWS_REGION=us-east-1

# 2. Enable Identity Center (via AWS Console)
# Go to: https://console.aws.amazon.com/singlesignon
# Click "Enable"
# 
# This creates your IdC instance and gives you:
# - Start URL: https://d-xxxxxxxxxx.awsapps.com/start
# - Identity source: (default) Identity Center directory
```

#### Step 2: Connect Your IdP via SAML

**Option A: External IdP (Okta, Azure AD, Auth0)**

Follow your IdP-specific guide:
- **Okta:** [providers/okta-setup.md](providers/okta-setup.md) *(coming soon)*
- **Azure AD:** [providers/microsoft-entra-id-setup.md](providers/microsoft-entra-id-setup.md) *(coming soon)*
- **Auth0:** [providers/auth0-setup.md](providers/auth0-setup.md) *(coming soon)*

**Option B: Identity Center Directory (Built-in)**

If you don't have an external IdP:

1. In IdC console, go to **Settings** → **Identity source**
2. Default: **Identity Center directory** (AWS-managed user directory)
3. Click **Users** → **Add user**
4. Create test user for validation
5. Click **Groups** → **Create group**
6. Name: `Codex-Developers`
7. Add users to group

#### Step 3: Deploy Infrastructure

```bash
# 1. Run wizard
cd source/
uv sync
uv run cxwb init

# Select: IAM Identity Center path
# Answer prompts with your IdC details from Step 1

# 2. Deploy stack
uv run cxwb deploy --profile codex-bedrock

# 3. Create permission set (see "AWS Console Steps" in Path A above)

# 4. Generate developer bundle
uv run cxwb distribute --profile codex-bedrock --bucket my-bucket
```

---

## Manual Deployment (Without `cxwb` Wizard)

**If you prefer manual CloudFormation deployment:**

### Step 1: Deploy Bedrock Auth Stack

```bash
# Set variables
AWS_REGION=us-west-2              # Bedrock region
STACK_NAME=codex-bedrock-idc
TEMPLATE_FILE=deployment/infrastructure/bedrock-auth-idc.yaml

# Deploy CloudFormation
aws cloudformation deploy \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE_FILE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      BedrockRegion="$AWS_REGION"

# Wait for completion (2-3 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION"

# Get outputs
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs'

# Note the PolicyArn output
```

**Stack creates:**
- IAM Role: `BedrockCognitoFederatedRole`
- IAM Policy: `CodexBedrockPolicy` (scoped to `bedrock:InvokeModel`)
- Trust relationship: Trusted by `sso.amazonaws.com`

### Step 2: Create Permission Set

See "AWS Console Steps" in Path A above.

### Step 3: Generate Developer Bundle

```bash
cd deployment/scripts/

./generate-codex-sso-config.sh \
  --start-url https://d-xxxxxxxxxx.awsapps.com/start \
  --sso-region us-east-1 \
  --account-id 123456789012 \
  --permission-set CodexBedrockUser \
  --bedrock-region us-west-2 \
  --profile-name codex-bedrock \
  --model openai.gpt-5.4 \
  --outdir ./codex-sso-config

# Optional: Add OTel monitoring
# --otel-endpoint http://otel-alb-xxxxx.us-west-2.elb.amazonaws.com
```

### Step 4: Distribute to Developers

**Option 1: Manual sharing**
```bash
zip -r codex-sso-config.zip codex-sso-config/
# Email or share via internal file sharing
```

**Option 2: S3 presigned URLs**
```bash
aws s3 cp codex-sso-config.zip s3://my-bucket/codex-sso-config.zip
aws s3 presign s3://my-bucket/codex-sso-config.zip --expires-in 604800
# Share URL (valid 7 days)
```

**Option 3: Self-service landing page**

See [distribution/landing-page.md](distribution/landing-page.md) *(coming soon)*

---

## Developer Installation

**Developers receive the bundle and run:**

```bash
# 1. Extract bundle
# The zip name matches the admin's profile: <profile-name>-config.zip
unzip <profile-name>-config.zip
cd <profile-name>-config/

# 2. Run installer
./install.sh

# This script:
# - Installs codex-sso-creds to ~/.local/bin/
# - Appends managed blocks to ~/.aws/config
# - Appends managed blocks to ~/.codex/config.toml
# - Creates backups of modified files

# 3. Authenticate with IdC
aws sso login --profile codex-bedrock

# Browser opens → User logs in with corporate credentials
# Token cached for 8-12 hours (session duration)

# 4. Verify access
aws sts get-caller-identity --profile codex-bedrock

# Expected output:
# {
#   "UserId": "AROA...:user@company.com",
#   "Account": "123456789012",
#   "Arn": "arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_CodexBedrockUser_.../user@company.com"
# }

# 5. Launch Codex
codex

# Codex reads ~/.codex/config.toml:
# - model_provider = "amazon-bedrock"
# - model = "openai.gpt-5.4"
# - region = "us-west-2"
# - profile = "codex-bedrock"

# Codex uses AWS SDK → reads ~/.aws/config:
# - [profile codex-bedrock]
# - credential_process = ~/.local/bin/codex-sso-creds ...

# codex-sso-creds:
# - Checks if SSO token is valid
# - If expired → runs `aws sso login` (browser opens)
# - Returns AWS credentials to Codex

# Codex makes Bedrock API call with SigV4 signing
```

---

## Validation

### Test Authentication

```bash
# 1. Check SSO token is valid
aws sso login --profile codex-bedrock

# 2. Get temporary credentials
aws configure export-credentials --profile codex-bedrock --format process | jq

# Expected output:
# {
#   "Version": 1,
#   "AccessKeyId": "ASIA...",
#   "SecretAccessKey": "...",
#   "SessionToken": "...",
#   "Expiration": "2026-05-11T18:30:00Z"
# }

# 3. Test Bedrock access
aws bedrock-runtime invoke-model \
  --model-id openai.gpt-5.4 \
  --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}' \
  --region us-west-2 \
  --profile codex-bedrock \
  output.json

cat output.json | jq
```

### Test Codex Integration

```bash
# 1. Check Codex config
cat ~/.codex/config.toml | grep -A5 "model_provider"

# Expected:
# model_provider = "amazon-bedrock"
# model = "openai.gpt-5.4"
# [model_providers.amazon-bedrock.aws]
# region = "us-west-2"
# profile = "codex-bedrock"

# 2. Run Codex test prompt
echo "Create a hello world function in Python" | codex

# Expected: Codex generates Python code using Bedrock
```

---

## Optional: Add Monitoring (OTel)

**If you want CloudWatch dashboards for usage tracking:**

### Step 1: Deploy OTel Stack

```bash
cd deployment/scripts/

./deploy-otel-stack.sh \
  --region us-west-2 \
  --profile codex-bedrock

# This deploys 3 stacks:
# 1. codex-networking (VPC, subnets)
# 2. codex-otel-collector (ECS Fargate + ALB)
# 3. codex-otel-dashboard (CloudWatch dashboard)

# Note the ALB URL from outputs:
# http://otel-alb-xxxxx.us-west-2.elb.amazonaws.com
```

### Step 2: Regenerate Bundle with OTel Endpoint

```bash
cd deployment/scripts/

./generate-codex-sso-config.sh \
  --start-url https://d-xxxxxxxxxx.awsapps.com/start \
  --sso-region us-east-1 \
  --account-id 123456789012 \
  --permission-set CodexBedrockUser \
  --bedrock-region us-west-2 \
  --profile-name codex-bedrock \
  --model openai.gpt-5.4 \
  --otel-endpoint http://otel-alb-xxxxx.us-west-2.elb.amazonaws.com \
  --outdir ./codex-sso-config-with-otel

# Redistribute new bundle to developers
```

**What changes:**
- `~/.codex/config.toml` now includes `[otel]` section
- Codex automatically exports metrics to CloudWatch
- View dashboard: CloudWatch → Dashboards → `CodexOnBedrock`

---

## Troubleshooting

### Issue: `aws sso login` fails with "Invalid start URL"

**Cause:** IdC start URL is incorrect or region mismatch

**Fix:**
```bash
# Verify IdC configuration
aws sso list-instances --region us-east-1 | jq

# Check start URL in ~/.aws/config
cat ~/.aws/config | grep sso_start_url
```

### Issue: "AccessDeniedException" when calling Bedrock

**Cause:** Permission set not attached or policy missing `bedrock:InvokeModel`

**Fix:**
1. Verify permission set assignment in IdC console
2. Check policy ARN is attached to permission set
3. Wait 5 minutes for propagation
4. Re-run `aws sso login --profile codex-bedrock`

### Issue: Codex says "No credentials found"

**Cause:** `credential_process` not configured correctly

**Fix:**
```bash
# Check ~/.aws/config has credential_process directive
cat ~/.aws/config | grep -A2 "profile codex-bedrock"

# Expected:
# [profile codex-bedrock]
# region = us-west-2
# credential_process = sh -c 'exec "$HOME/.local/bin/codex-sso-creds" ...'

# Test credential_process manually
sh -c 'exec "$HOME/.local/bin/codex-sso-creds" codex-bedrock-sso codex-bedrock' | jq
```

### Issue: Browser doesn't open for SSO login

**Cause:** `codex-sso-creds` can't find AWS CLI

**Fix:**
```bash
# Check AWS CLI is in PATH
which aws

# If not found, install:
# macOS: brew install awscli
# Linux: sudo apt install awscli
# Windows: winget install Amazon.AWSCLI

# Or specify full path in codex-sso-creds script
```

### More troubleshooting

See [operate-troubleshooting.md](operate-troubleshooting.md)

---

## Cleanup

**To remove the Native AWS Access deployment:**

```bash
# 1. Developers uninstall locally
./uninstall.sh

# This removes:
# - ~/.local/bin/codex-sso-creds
# - Managed blocks from ~/.aws/config
# - Managed blocks from ~/.codex/config.toml

# 2. Admin deletes CloudFormation stack
aws cloudformation delete-stack \
  --stack-name codex-bedrock-idc \
  --region us-west-2

# 3. Admin removes permission set (optional)
# In IdC console:
# - Multi-account permissions → Permission sets
# - Select CodexBedrockUser → Delete
```

---

---

## Next Steps

- **Add monitoring:** [Optional: Add Monitoring](#optional-add-monitoring-otel)
- **Migrate to LLM Gateway:** [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md)
- **Scale to more users:** Distribute bundle via self-service landing page
- **Monitor costs:** Set up CloudWatch alarms on Bedrock spend

---

## Support

- **Documentation:** [../QUICKSTART.md](../QUICKSTART.md)
- **Issues:** [GitHub Issues](https://github.com/aws-samples/guidance-for-codex-on-aws/issues)
- **Technical guide:** [deploy-identity-center.md](deploy-identity-center.md)
