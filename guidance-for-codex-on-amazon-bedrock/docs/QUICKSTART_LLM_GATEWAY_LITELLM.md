# Quick Start: LiteLLM Gateway on AWS

> **Status:** Reference Implementation  
> **Audience:** Organizations evaluating LLM gateway patterns, learning CloudFormation deployment  
> **Production Readiness:** Requires security hardening before production use (see [Security Considerations](#security-considerations))

Deploy LiteLLM gateway on ECS Fargate for OpenAI Codex with Amazon Bedrock backend. This is the AWS-maintained reference implementation of the [LLM Gateway pattern](QUICKSTART_LLM_GATEWAY.md).

**Features:**
- Per-user and per-team budget limits (`max_budget`, `budget_duration`)
- Rate limiting (RPM and TPM controls)
- Model routing and fallback
- Admin API for key generation
- Optional OIDC self-service portal
- CloudWatch metrics via OpenTelemetry

---

## Prerequisites

- AWS account with admin permissions (ECS, VPC, ALB, RDS, CloudFormation, ECR, Secrets Manager)
- Amazon Bedrock activated in target region (this walkthrough uses `us-east-1`)
- AWS CLI v2 installed and authenticated
- Docker installed and running
- `jq` for parsing CloudFormation outputs (optional but recommended)
- [Codex CLI](https://developers.openai.com/codex/cli) installed
- ACM certificate in `us-east-1` for the HTTPS hostname you want the gateway to use
- For trusted Codex/browser HTTPS, a DNS name you control must resolve to the ALB and match that ACM certificate

---

## Deployment

### Step 1: Clone and Set Variables

```bash
git clone https://github.com/aws-samples/sample-openai-on-aws.git
cd sample-openai-on-aws/guidance-for-codex-on-amazon-bedrock

export AWS_REGION=us-east-1
export BEDROCK_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
export ALB_CERTIFICATE_ARN=arn:aws:acm:us-east-1:123456789012:certificate/replace-me
export ALLOWED_CIDR="$(curl -Ls https://checkip.amazonaws.com)/32"

# Optional but recommended for trusted HTTPS.
# If you omit this, the stack returns the ALB DNS name and you'll need `curl -k`
# for low-level smoke tests because the ACM certificate will not match the ALB hostname.
# Codex itself should use a cert-matching hostname, not the raw ALB DNS name.
export GATEWAY_DOMAIN_NAME=gateway.example.com
```

### Step 2: Build and Push LiteLLM Image

```bash
# Create ECR repository
export LITELLM_REPO=codex-litellm
aws ecr create-repository \
  --repository-name "$LITELLM_REPO" \
  --region "$AWS_REGION" \
  --image-scanning-configuration scanOnPush=true \
  || echo "Repository already exists"

# Authenticate Docker to ECR
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

# Build and push
export LITELLM_VERSION=main-latest
export LITELLM_IMAGE_TAG=v1
export LITELLM_IMAGE="$ECR_REGISTRY/$LITELLM_REPO:$LITELLM_IMAGE_TAG"

docker buildx create --use --name codex-builder 2>/dev/null || true
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg LITELLM_VERSION="$LITELLM_VERSION" \
  --tag "$LITELLM_IMAGE" \
  --file deployment/litellm/Dockerfile \
  --push \
  deployment/litellm
```

**For single-arch (faster, recommended on Apple Silicon):**
```bash
docker buildx build \
  --builder codex-builder \
  --platform linux/amd64 \
  --build-arg LITELLM_VERSION="$LITELLM_VERSION" \
  --tag "$LITELLM_IMAGE" \
  --file deployment/litellm/Dockerfile \
  --push \
  deployment/litellm
```

### Step 3: Deploy Networking

```bash
export NETWORKING_STACK=codex-networking

aws cloudformation deploy \
  --stack-name "$NETWORKING_STACK" \
  --template-file deployment/infrastructure/networking.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides VpcCidr=10.0.0.0/16
```

### Step 4 (Optional): Deploy OTel Collector

For CloudWatch metrics.

This step requires a Route53 hosted zone because
`deployment/infrastructure/otel-collector.yaml` creates an ACM certificate and
DNS record automatically. If you do not want to use Route53 for the collector,
skip this step and keep `EnableOtel="false"` in Step 6.

```bash
export OTEL_STACK=codex-otel-collector
export OTEL_DOMAIN_NAME=telemetry.example.com
export OTEL_HOSTED_ZONE_ID=Z1234567890ABC

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
      CustomDomainName="$OTEL_DOMAIN_NAME" \
      HostedZoneId="$OTEL_HOSTED_ZONE_ID"
```

### Step 5 (Optional): Deploy User-Key-Mapping for OIDC

Only if enabling OIDC self-service:

```bash
export USERKEY_STACK=codex-user-key-mapping

aws cloudformation deploy \
  --stack-name "$USERKEY_STACK" \
  --template-file deployment/litellm/ecs/user-key-mapping.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides TableName=codex-user-keys
```

### Step 6: Deploy LiteLLM Gateway

```bash
export GATEWAY_STACK=codex-litellm-gateway
export MASTER_KEY=$(openssl rand -hex 32)
# RDS rejects '/', '@', double quotes, and spaces in MasterUserPassword.
export DB_PASSWORD="$(openssl rand -base64 24 | tr -d '/+=')"

# Deploy gateway (references networking stack via imports)
aws cloudformation deploy \
  --stack-name "$GATEWAY_STACK" \
  --template-file deployment/litellm/ecs/litellm-ecs.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      NetworkingStackName="$NETWORKING_STACK" \
      EnableOtel="false" \
      LiteLLMMasterKey="$MASTER_KEY" \
      DBUsername=litellm \
      DBPassword="$DB_PASSWORD" \
      AwsRegion="$BEDROCK_REGION" \
      LiteLLMImage="$LITELLM_IMAGE" \
      AlbCertificateArn="$ALB_CERTIFICATE_ARN" \
      AllowedCidr="$ALLOWED_CIDR" \
      EnableJwtMiddleware="false"

# For trusted HTTPS, add:
#     AlbDomainName="$GATEWAY_DOMAIN_NAME"
#
# If you deployed Step 4, also add:
#     OtelStackName="$OTEL_STACK"
#     EnableOtel="true"

# Save credentials
echo "LITELLM_MASTER_KEY=$MASTER_KEY" > .env.gateway
echo "DB_PASSWORD=$DB_PASSWORD" >> .env.gateway
chmod 600 .env.gateway

# Get gateway URL
export GATEWAY_URL=$(aws cloudformation describe-stacks \
  --stack-name "$GATEWAY_STACK" --region "$AWS_REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`GatewayEndpoint`].OutputValue' --output text)

echo "Gateway URL: $GATEWAY_URL"
```

The bundled LiteLLM image now uses LiteLLM's documented
`bedrock_mantle/openai.gpt-5.x` provider and refreshes
`AWS_BEARER_TOKEN_BEDROCK` in-process from the gateway task role using the
official `aws-bedrock-token-generator` package. That matches OpenAI's Bedrock
guidance for long-running applications: use a token provider rather than
manually injecting a static 12-hour bearer token.

If you omit `AlbDomainName`, CloudFormation returns `https://<alb-dns>/v1` as
`GatewayEndpoint`. That endpoint is useful for low-level smoke tests with
`curl -k`, but it is not a trusted Codex endpoint because the ACM certificate
does not match the raw ALB hostname.

---

## Developer Configuration

### Get API Key

#### Option A: Admin-Generated Keys

```bash
# Generate key for a user
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "alice@company.com",
    "user_id": "alice@company.com",
    "models": ["gpt-5.5", "gpt-5.4", "gpt-oss-120b"],
    "max_budget": 50.0,
    "budget_duration": "30d",
    "tpm_limit": 100000,
    "rpm_limit": 1000
  }'

# Returns: {"key": "sk-litellm-..."}
```

#### Option B: Self-Service OIDC

If you deployed with `EnableJwtMiddleware=true`, see [deployment/litellm/jwt-middleware/README.md](../deployment/litellm/jwt-middleware/README.md) for OIDC setup.

### Codex Configuration

Developers add this to the user-level `~/.codex/config.toml`:

```toml
model_provider = "litellm-gateway"
model = "gpt-5.5"         # Preferred latest GPT-5 model when available
web_search = "disabled"   # Bedrock Mantle does not accept the hosted web_search tool type

[model_providers.litellm-gateway]
name = "LiteLLM Gateway"
base_url = "<gateway-endpoint>"  # Paste the exact GatewayEndpoint value, including scheme and /v1
env_key = "OPENAI_API_KEY"
wire_api = "responses"    # Optional but explicit; custom providers default to Responses
```

> **Note:** Bedrock Mantle serves GPT-5.x through the Responses API, so `wire_api = "responses"` is the right setting here. Codex custom providers already default to Responses; this guide keeps the setting explicit because it makes the Mantle dependency obvious. `web_search = "disabled"` is a Bedrock Mantle compatibility choice, not a general OpenAI recommendation. The bundled LiteLLM image refreshes its upstream Mantle bearer token automatically from the gateway's AWS credential chain. For Codex itself, `base_url` should be a trusted HTTPS hostname whose certificate matches the URL. Keep this provider block in user-level `~/.codex/config.toml`; Codex ignores provider and auth settings in project-local `.codex/config.toml`.

Set API key:

```bash
# macOS / Linux
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx' >> ~/.zshrc
source ~/.zshrc

# Windows PowerShell (replace sk-litellm-xxx with actual key from /key/generate)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-litellm-xxxxxxxxxxxxx", "User")
```

Test:

```bash
codex exec "Create a hello world function in Python"

# Expected: Codex returns Python code, no auth/connection errors
```

---

## Quota Management

### Per-User Budgets

```bash
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "bob@company.com",
    "max_budget": 100.0,
    "budget_duration": "30d"
  }'
```

### Per-Team Budgets

```bash
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "platform-team",
    "max_budget": 500.0,
    "budget_duration": "30d",
    "tpm_limit": 100000,
    "rpm_limit": 1000
  }'
```

### Check Usage

```bash
curl -X GET "$GATEWAY_URL/user/info" \
  -H "Authorization: Bearer $USER_API_KEY"
```

**Documentation:**
- [LiteLLM User Budgets](https://docs.litellm.ai/docs/proxy/users)
- [LiteLLM Team Budgets](https://docs.litellm.ai/docs/proxy/team_budgets)
- [LiteLLM Rate Limiting](https://docs.litellm.ai/docs/proxy/rate_limit_tiers)

---

## Monitoring

If you deployed the OTel collector (Step 4), metrics flow to CloudWatch
namespace `LiteLLMGateway` by default unless you override `MetricsNamespace` in
the collector stack:

```bash
aws cloudwatch list-metrics \
  --namespace LiteLLMGateway \
  --region "$AWS_REGION" \
  --query 'Metrics[0:5].[MetricName]' \
  --output table
```

**Metrics available:**
- `gen_ai.client.operation.duration` - Request latency
- `gen_ai.client.token.usage` - Token usage
- `litellm.request_total_cost_usd` - Request costs

**Dashboard:**
```bash
aws cloudformation deploy \
  --stack-name codex-litellm-dashboard \
  --template-file deployment/infrastructure/litellm-dashboard.yaml \
  --parameter-overrides MetricsNamespace=LiteLLMGateway \
  --region "$AWS_REGION"
```

---

## Troubleshooting

### Gateway returns 500 "Database connection failed"

**Cause:** RDS not accessible from ECS tasks

**Fix:**
```bash
aws logs tail "/ecs/$GATEWAY_STACK" --follow --region "$AWS_REGION"

# Check security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:aws:cloudformation:stack-name,Values=$GATEWAY_STACK" \
  --query 'SecurityGroups[*].[GroupId,GroupName]'
```

### Gateway returns 403 "AccessDeniedException" calling Bedrock

**Cause:** ECS task role missing Bedrock permissions

**Fix:**
```bash
# Get task role name from stack resources
TASK_ROLE=$(aws cloudformation describe-stack-resource \
  --stack-name "$GATEWAY_STACK" --region "$AWS_REGION" \
  --logical-resource-id TaskRole \
  --query 'StackResourceDetail.PhysicalResourceId' --output text)

aws iam list-attached-role-policies --role-name "$TASK_ROLE"
```

### Codex returns 401 "Unauthorized"

**Cause:** API key wrong or expired

**Fix:**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test key directly
curl -X POST "$GATEWAY_URL/v1/responses" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.5","input":"test"}'
```

If `GATEWAY_URL` uses the raw ALB DNS name instead of a cert-matching domain,
add `-k` for this low-level smoke test.

### Request to a specific model hangs, then returns 504 Gateway Time-out

**Cause:** The requested model is not served by Bedrock Mantle in your region or
is not enabled for your account. The upstream call never returns and the ALB
closes the connection at its idle timeout (~60s). In testing, `gpt-5.5`
returned normally while `gpt-5.4` timed out in the same region/account.

**Fix:**
```bash
# Prefer gpt-5.5 (the recommended Codex model). Confirm the model works:
curl -X POST "$GATEWAY_URL/responses" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.5","input":"ping"}'
```

If a specific model times out, verify it is available for your account and
region (see [reference-regions.md](reference-regions.md)) and request model
access in the **Amazon Bedrock → Model access** console before relying on it.

### Codex fails TLS verification but `curl -k` works

**Cause:** `GatewayEndpoint` is using the raw ALB DNS name while the ACM
certificate is issued for a different hostname.

**Fix:**
```bash
# Deploy or update the stack with a DNS name that resolves to the ALB and
# matches the ACM certificate.
AlbDomainName="$GATEWAY_DOMAIN_NAME"
```

Use the raw ALB DNS name only for low-level `curl -k` smoke tests.

### Docker build fails

**Cause:** Docker not running

**Fix:**
```bash
docker ps
# If error, start Docker Desktop
```

---

## Security Considerations

This reference implementation demonstrates the LLM gateway pattern but requires security hardening before production use:

**Known Security Gaps:**
1. **Database Credentials** - Master key and DB password stored in plaintext (use AWS Secrets Manager rotation)
2. **Network Exposure** - Default AllowedCidr permits VPC-wide access (use least-privilege CIDR)
3. **RDS Encryption Scope** - RDS is already hardcoded to `PubliclyAccessible: false`; for production also review snapshot sharing, IAM auth, and CMK usage
4. **Encryption** - Missing encryption-at-rest for ALB logs and ECS volumes
5. **IAM Permissions** - Task role uses wildcard Bedrock permissions (scope to specific model ARNs)
6. **DynamoDB** - User-key-mapping table lacks KMS CMK with key rotation
7. **Logging** - No VPC Flow Logs, GuardDuty, or Security Hub integration

**Hardening Checklist:**
- [ ] Rotate credentials via Secrets Manager
- [ ] Enable encryption-at-rest for all data stores (ALB logs, ECS, DynamoDB with CMK)
- [ ] Implement least-privilege IAM (specific Bedrock model ARNs)
- [ ] Deploy WAF rules on ALB
- [ ] Enable VPC Flow Logs and GuardDuty
- [ ] Configure Security Hub benchmarks (CIS AWS Foundations)
- [ ] Add resource tagging for cost allocation

For production deployments, see [AWS Well-Architected Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html).

---

## Cleanup

```bash
# Delete gateway stack
aws cloudformation delete-stack --stack-name "$GATEWAY_STACK" --region "$AWS_REGION"

# Delete optional stacks
aws cloudformation delete-stack --stack-name "$USERKEY_STACK" --region "$AWS_REGION"
aws cloudformation delete-stack --stack-name "$OTEL_STACK" --region "$AWS_REGION"

# Delete networking (wait for above to complete first)
aws cloudformation wait stack-delete-complete --stack-name "$GATEWAY_STACK" --region "$AWS_REGION"
aws cloudformation delete-stack --stack-name "$NETWORKING_STACK" --region "$AWS_REGION"

# Delete ECR images
aws ecr delete-repository --repository-name "$LITELLM_REPO" --region "$AWS_REGION" --force

# Developers remove config
# Delete litellm-gateway block from ~/.codex/config.toml
# unset OPENAI_API_KEY
```

---

## Advanced Configuration

### Model Routing

Edit `deployment/litellm/litellm_config.yaml`:

```yaml
model_list:
  - model_name: gpt-5.4
    litellm_params:
      model: bedrock_mantle/openai.gpt-5.4

  - model_name: gpt-5.5
    litellm_params:
      model: bedrock_mantle/openai.gpt-5.5
```

> **Note on GPT-5.4 / GPT-5.5:** These models are Responses-only on Bedrock Mantle. The `bedrock_mantle/` prefix keeps LiteLLM on its documented Mantle Responses provider, which preserves the OpenAI Responses payload shape Codex expects. Prefer `gpt-5.5` when you want the latest OpenAI-recommended Codex model; keep `gpt-5.4` when you need broader Bedrock regional coverage. The bundled LiteLLM image refreshes `AWS_BEARER_TOKEN_BEDROCK` automatically from the gateway's AWS credential chain, and LiteLLM derives the Mantle endpoint from the selected region. GPT-5.4 is also available in `us-west-2` — see `reference-regions.md` if you prefer a different region.

Rebuild and redeploy the image (Steps 2 & 6).

### Custom JWT Middleware

For OIDC self-service portal, see [deployment/litellm/jwt-middleware/README.md](../deployment/litellm/jwt-middleware/README.md).

---

## Support

- **LiteLLM Documentation:** [docs.litellm.ai](https://docs.litellm.ai)
- **Pattern Documentation:** [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md)
- **Issues:** [GitHub Issues](https://github.com/aws-samples/sample-openai-on-aws/issues)
- **Codex Configuration:** [OpenAI Codex docs](https://developers.openai.com/codex/config-advanced)
