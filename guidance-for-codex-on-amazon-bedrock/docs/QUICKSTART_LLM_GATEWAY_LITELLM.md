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
- Amazon Bedrock activated in target region (e.g., `us-west-2`)
- AWS CLI v2 installed and authenticated
- Docker installed and running
- `jq` for parsing CloudFormation outputs (optional but recommended)
- [Codex CLI](https://developers.openai.com/codex/cli) installed

---

## Deployment

### Step 1: Clone and Set Variables

```bash
git clone https://github.com/aws-samples/sample-openai-on-aws.git
cd sample-openai-on-aws/guidance-for-codex-on-amazon-bedrock

export AWS_REGION=us-west-2
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
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

**For single-arch (faster):**
```bash
docker build --build-arg LITELLM_VERSION=$LITELLM_VERSION -t $LITELLM_IMAGE deployment/litellm
docker push $LITELLM_IMAGE
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

For CloudWatch metrics:

```bash
export OTEL_STACK=codex-otel-collector

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
      SubnetIds="$SUBNET_IDS"
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
export DB_PASSWORD=$(openssl rand -base64 32)

# Generate a short-term Bedrock Mantle API key scoped to us-east-2 (valid 12h)
# Both gpt-5.4 and gpt-5.5 use us-east-2 endpoints — key must match
pip install aws-bedrock-token-generator -q
export BEDROCK_MANTLE_KEY=$(AWS_DEFAULT_REGION=us-east-2 python -c "from aws_bedrock_token_generator import provide_token; print(provide_token())")

# Deploy gateway (references networking stack via imports)
aws cloudformation deploy \
  --stack-name "$GATEWAY_STACK" \
  --template-file deployment/litellm/ecs/litellm-ecs.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      NetworkingStackName="$NETWORKING_STACK" \
      OtelStackName="$OTEL_STACK" \
      EnableOtel="true" \
      LiteLLMMasterKey="$MASTER_KEY" \
      BedrockMantleApiKey="$BEDROCK_MANTLE_KEY" \
      DBPassword="$DB_PASSWORD" \
      AwsRegion="$AWS_REGION" \
      LiteLLMImage="$LITELLM_IMAGE" \
      AllowedCidr="10.0.0.0/8" \
      EnableJwtMiddleware="false"

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
    "models": ["gpt-4o", "gpt-4o-mini", "gpt-oss-120b"],
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

Developers add this to `~/.codex/config.toml`:

```toml
model_provider = "litellm-gateway"
model = "gpt-5.5"
web_search = "disabled"   # Bedrock Mantle does not support the web_search tool type

[model_providers.litellm-gateway]
name = "LiteLLM Gateway"
base_url = "http://<gateway-url>/v1"
env_key = "OPENAI_API_KEY"
wire_api = "responses"    # Codex 0.136+ calls /v1/responses directly; must match
```

> **Note:** `wire_api = "responses"` is required for GPT-5.x because these models only support the Responses API. `web_search = "disabled"` prevents Codex from sending a tool type that Bedrock Mantle does not accept. Both settings are required for requests to succeed.

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

If you deployed the OTel collector (Step 4), metrics flow to CloudWatch namespace `Codex`:

```bash
aws cloudwatch list-metrics \
  --namespace Codex \
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
  --region "$AWS_REGION"
```

---

## Troubleshooting

### Gateway returns 500 "Database connection failed"

**Cause:** RDS not accessible from ECS tasks

**Fix:**
```bash
aws logs tail /ecs/codex-gateway --follow --region "$AWS_REGION"

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
curl -X POST "$GATEWAY_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.4","messages":[{"role":"user","content":"test"}]}'
```

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
3. **RDS Public Access** - Template allows `PubliclyAccessible: true` parameter (disable for production)
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
      model: openai/openai.gpt-5.4
      api_key: os.environ/BEDROCK_MANTLE_API_KEY
      api_base: "https://bedrock-mantle.us-east-2.api.aws/openai/v1"

  - model_name: gpt-5.5
    litellm_params:
      model: openai/openai.gpt-5.5
      api_key: os.environ/BEDROCK_MANTLE_API_KEY
      api_base: "https://bedrock-mantle.us-east-2.api.aws/openai/v1"
```

> **Note on GPT-5.4 / GPT-5.5:** These models only support the Responses API. The `openai/` prefix tells LiteLLM to proxy the request to the OpenAI-compatible Bedrock Mantle endpoint as-is — no additional routing needed because Codex (v0.136+) already calls `/v1/responses` directly via `wire_api = "responses"`. Both endpoints use `us-east-2` so a single `BEDROCK_MANTLE_API_KEY` (generated with `AWS_DEFAULT_REGION=us-east-2`) covers both models. GPT-5.4 is also available in `us-west-2` — see `reference-regions.md` if you prefer a different region.

Rebuild and redeploy the image (Steps 2 & 6).

### Custom JWT Middleware

For OIDC self-service portal, see [deployment/litellm/jwt-middleware/README.md](../deployment/litellm/jwt-middleware/README.md).

---

## Support

- **LiteLLM Documentation:** [docs.litellm.ai](https://docs.litellm.ai)
- **Pattern Documentation:** [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md)
- **Issues:** [GitHub Issues](https://github.com/aws-samples/sample-openai-on-aws/issues)
- **Codex Configuration:** [OpenAI Codex docs](https://developers.openai.com/codex/config-advanced)
