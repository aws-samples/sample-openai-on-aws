# Quick Start: LLM Gateway

Deploy Codex on Bedrock with LiteLLM gateway for hard quota enforcement and centralized policy control.

**Use this pattern if:**
- ✅ You need hard per-user/per-team budget limits (request blocking)
- ✅ You need rate limiting (RPM/TPM enforcement)
- ✅ You don't use IdC and don't want to set it up
- ✅ You need centralized model routing or automatic fallback

---

## Overview

**What You're Deploying:**
```
Corporate IdP (Okta/Azure) → OIDC → LiteLLM Gateway → Bedrock
                                        ↓
                               Hard quota enforcement
                               Rate limiting (RPM/TPM)
                               Model routing/fallback
```

---

## Prerequisites

### Required

- [ ] AWS account with admin permissions (ECS, VPC, ALB, RDS, CloudFormation)
- [ ] Amazon Bedrock activated in target region (e.g., `us-west-2`)
- [ ] AWS credentials configured (one of):
  - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
  - Credentials file (`~/.aws/credentials`)
  - AWS SSO profile
- [ ] Python 3.10-3.13 + uv ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- [ ] Docker installed and running (for building LiteLLM container image)

### Optional (For OIDC Self-Service)

- [ ] Identity provider with OIDC support (Okta, Azure AD, Auth0, Cognito)
- [ ] JWKS URL from your IdP (e.g., `https://tenant.okta.com/.well-known/jwks.json`)

**Note:** OIDC self-service is available via the **custom JWT middleware** shipped in this guidance. See [Option B: Self-Service OIDC](#option-b-self-service-oidc-portal-custom-jwt-middleware) for setup.

---

## Deployment Options

### Option A: Wizard (Recommended)

**Four main commands:**
1. `uv run cxwb init` — Configure deployment
2. `uv run cxwb build` — Build Docker images  
3. `uv run cxwb deploy` — Deploy infrastructure
4. `uv run cxwb distribute` — Generate developer bundle

**Full workflow:**

```bash
# 1. Clone repo
git clone https://github.com/aws-samples/guidance-for-codex-on-aws.git
cd guidance-for-codex-on-aws/guidance-for-codex-on-amazon-bedrock

# 2. Install CLI
cd source/
uv sync

# 3. Run wizard
uv run cxwb init

# Select: Gateway path
# Answer prompts:
# - Deployment path? → LiteLLM Gateway — deploy new
# - AWS region? → us-west-2
# - LiteLLM Docker image? → Build automatically (Recommended)
# - LiteLLM version? → v1.61.29 (Recommended)
# - Enable OIDC/SSO? → No (use admin keys) OR Yes (self-service)
#   
#   If Yes to OIDC:
#   - JWKS URL? → https://your-tenant.okta.com/.well-known/jwks.json
#   - JWT Audience? → (optional, your client ID)
#   - JWT Issuer? → (optional, your IdP URL)
#
# - Enable OpenTelemetry monitoring? → Yes (Recommended)
# - Monitoring mode? → 
#     • Local collectors only (Default - no ECS needed)
#     • Central collector only (Server-side only)
#     • Hybrid
#     • None (Disable monitoring)
#
# - LiteLLM master key? → (auto-generated)
# - Database password? → (auto-generated)
# - Allowed CIDR? → 10.0.0.0/8 (corporate network)
# - Default model? → openai.gpt-oss-safeguard-120b
# - Profile name? → codex-gateway

# 4. Build Docker images
# If OIDC enabled, build JWT middleware first:
uv run cxwb build-jwt --profile <profile-name>  # Only if OIDC enabled

# Build LiteLLM image:
uv run cxwb build --profile <profile-name>

# This:
# - Builds multi-arch Docker images (ARM64 + x86_64)
# - Creates ECR repositories
# - Pushes images to ECR
# - Updates profile with image URIs

# 5. Deploy infrastructure
uv run cxwb deploy --profile <profile-name>

# This deploys stacks in order (based on monitoring mode):
# 1. codex-otel-networking (VPC, subnets, NAT gateway)
# 2. codex-otel-collector (OpenTelemetry collector - if Central or Hybrid mode)
# 3. codex-user-key-mapping (DynamoDB table - if OIDC enabled)
# 4. codex-litellm-gateway (ECS Fargate + ALB + LiteLLM + JWT middleware)

# Wait 10-15 minutes for deployment
# Outputs:
# - GatewayEndpoint = http://<alb-url>/v1
# - If OIDC enabled: Self-service portal at http://<alb-url>/api/my-key
# - If Central/Hybrid mode: CollectorEndpoint = http://<otel-alb-url>

# 6. Download local OTEL collector binary (ONLY if Local or Hybrid mode)
# IMPORTANT: This step packages the binary into the developer bundle
# Developers do NOT need to download this separately - it comes in the bundle
cd ../deployment/scripts
./build-local-collector.sh --platform darwin-arm64
# Downloads ~15MB binary to ../binaries/ (excluded from git via .gitignore)
# Supports: darwin-arm64, darwin-amd64, linux-amd64, windows-amd64

# 7. Generate developer bundle
# This command packages everything including the binary from step 6
cd ../../source
uv run cxwb distribute --profile <profile-name> --bucket my-bucket

# Output: S3 presigned URL for developers to download
# Bundle includes:
#   • Gateway config (config.toml)
#   • OTEL collector binary (packaged from step 6 if Local/Hybrid mode)
#   • Collector config + management scripts
#   • install.sh (installs everything on developer machine)
```

**Bundle contents:**
```
<profile-name>-config/
├── install.sh              # Developer runs this
├── uninstall.sh            # Cleanup script
├── refresh-key.sh          # Optional: refresh expired API key
├── config.toml.snippet     # Codex config fragment
├── DEV-SETUP.md            # Developer instructions with gateway URL
└── env.template            # Template for OPENAI_API_KEY
```

---

---

## Developer Installation

**Getting your API key:** See [Getting API Key - Two Options](#getting-api-key---two-options) section below for how to obtain your key.

**Developers receive the bundle and:**

```bash
# 1. Extract bundle
# The zip is created in the dist/ folder of the project directory
# The zip name matches your profile: dist/<profile-name>-config.zip
unzip dist/<profile-name>-config.zip
cd <profile-name>-config/

# 2. Get API key from admin (see "Getting API Key - Two Options" section)

# 3. Run installer (will prompt for API key)
./install.sh

# The installer will:
# - Prompt for your LiteLLM Gateway API key (starts with sk-litellm-)
# - Validate the key format
# - Configure ~/.codex/config.toml with the key
# - Add codex-gateway alias to your shell profile
# - Remove any conflicting OpenAI authentication

# 4. Reload your shell
source ~/.zshrc  # macOS
source ~/.bashrc # Linux

# 5. Verify the alias was created
alias codex-gateway
# Should show: alias codex-gateway='codex -c model_provider="litellm-gateway" -c model="gpt-4o"'
```

**What is `codex-gateway`?**

The installer automatically creates a shell alias that configures Codex CLI to use your LiteLLM gateway:

```bash
alias codex-gateway='codex -c model_provider="litellm-gateway" -c model="gpt-4o"'
```

This alias:
- Sets the provider to `litellm-gateway` (instead of default OpenAI)
- Sets the model to `gpt-4o` (which gateway maps to Bedrock model)
- Reads your API key from `~/.codex/config.toml` (configured by install.sh)

**Without the alias, you would need to type:**
```bash
codex -c 'model_provider="litellm-gateway"' -c 'model="gpt-4o"' exec "your prompt"
```

The alias is a shortcut so you can just type `codex-gateway` instead.

---

## Testing Your Setup

After installation, verify both access methods work:

### Test 1: Codex CLI

```bash
# Test with the codex-gateway alias (created by install.sh)
codex-gateway exec "What is 2+2? Answer in one word."

# Expected output:
# Four
# 
# tokens used
# 45
```

**Verification checklist:**
- ✅ Command completes without errors
- ✅ You see a response from the model
- ✅ Token count is displayed at the end
- ✅ No mention of "api.openai.com" in output

**If you see errors:**
- `401 Unauthorized` → Check your API key is correct
- `Not inside a trusted directory` → Run from a git repo or add `--skip-git-repo-check`
- `provider: openai` → You're using wrong command, use `codex-gateway` not `codex`

### Test 2: Direct API (curl)

```bash
# Set environment variable (if not already set)
export OPENAI_API_KEY="sk-litellm-xxxxxxxxxxxxx"

# Test with curl
curl -X POST "http://<gateway-url>/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "What is 2+2? Answer in one word."}]
  }'

# Expected output:
# {
#   "id": "chatcmpl-...",
#   "object": "chat.completion",
#   "created": 1234567890,
#   "model": "gpt-4o",
#   "choices": [{
#     "index": 0,
#     "message": {
#       "role": "assistant",
#       "content": "Four"
#     },
#     "finish_reason": "stop"
#   }],
#   "usage": {
#     "prompt_tokens": 15,
#     "completion_tokens": 1,
#     "total_tokens": 16
#   }
# }
```

**Verification checklist:**
- ✅ Status code 200 OK
- ✅ Response contains "choices" array with model output
- ✅ Response contains "usage" object with token counts
- ✅ No error messages

**If you see errors:**
- `401 Unauthorized` → Check API key is set correctly: `echo $OPENAI_API_KEY`
- `Connection refused` → Check gateway URL is correct
- `Invalid model` → Gateway doesn't have model mapped (check litellm_config.yaml)

---

## Monitoring Options

This guidance supports **OpenTelemetry monitoring** with CloudWatch for usage tracking and cost attribution.

### Three Monitoring Modes

| Mode | Client Metrics | Server Metrics | Infrastructure | Monthly Cost | Best For |
|------|----------------|----------------|----------------|--------------|----------|
| **Local Only** | ✅ Yes | ❌ No | None | ~$10 | Small teams, quick start |
| **Central Only** | ❌ No | ✅ Yes | ECS + ALB | ~$31 | Server visibility only |
| **Hybrid** | ✅ Yes | ✅ Yes | ECS + ALB | ~$41 | Production (recommended) |

#### Local Collectors Only (Default)

**What you get:**
- Client-side metrics: E2E latency, tool usage, turn duration
- Lightweight binary (~15MB) runs on each developer machine
- Uses AWS SSO credentials (no infrastructure needed)
- CloudWatch dashboard for visualization

**Developer experience:**
```bash
# Automatically installed via install.sh
~/.codex/otel/start-collector.sh  # Start in background
~/.codex/otel/stop-collector.sh   # Stop collector
~/.codex/otel/collector-status.sh # Check status, memory usage
tail -f ~/.codex/otel/otelcol.log # View logs
```

**Metrics collected:**
- `codex.turn.duration_ms` - E2E latency per turn
- `codex.turn.token_usage` - Tokens by type (input, output, cached)
- `codex.api_request` - API calls, status codes
- Dimensions: user.email, model, session_source

#### Central Collector Only

**What you get:**
- Server-side metrics: API costs, token usage, gateway health
- ECS Fargate collector (0.5 vCPU, 1GB RAM)
- Cannot be disabled by developers
- Full audit trail in CloudWatch

**Metrics collected:**
- `gen_ai.client.operation.duration` - Request latency
- `gen_ai.client.token.usage` - Token usage from LiteLLM
- `litellm.request_total_cost_usd` - Request costs in USD
- Dimensions: OTelLib, gen_ai.operation.name

#### Hybrid (Recommended for Production)

**What you get:**
- **Complete visibility**: Client + Server metrics combined
- **Single dashboard**: Unified view of all metrics
- **User attribution**: Track costs per user/team/department
- **Best for**: Production deployments requiring full observability

### Configuration During Wizard

During `cxwb init`, you'll be prompted:
```
? Enable OpenTelemetry monitoring? Yes
? Monitoring mode:
  ❯ Local collectors only - Client metrics, no ECS (Default)
    Central collector only - Server metrics from gateway
    Hybrid (local + central) - Complete visibility (Recommended for prod)
    None - Disable monitoring
```

**Recommendation:**
- **Quick start / Evaluation:** Choose "Local collectors only"
- **Production deployment:** Choose "Hybrid"
- **Server-only visibility:** Choose "Central collector only"

---

## Testing OTEL Monitoring

### Test 1: Local Collector (if Local or Hybrid mode)

```bash
# Step 1: Verify local collector is installed
ls -lh ~/.codex/otel/
# Expected files:
# - otelcol-local (~15MB binary)
# - otel-config.yaml
# - start-collector.sh
# - stop-collector.sh
# - collector-status.sh

# Step 2: Start the collector
~/.codex/otel/start-collector.sh
# Expected output:
# Starting OTEL collector...
# ✓ OTEL collector started (PID 12345)
#   Sending metrics to: CloudWatch (region: us-west-2)
#   Logs: /Users/you/.codex/otel/otelcol.log

# Step 3: Check status
~/.codex/otel/collector-status.sh
# Expected output:
# ✓ Collector running
#   PID: 12345
#   Started: Thu May 14 10:45:00 2026
#   Memory: ~45MB
#   Region: us-west-2
#   User: your-email@example.com

# Step 4: Send test metric
curl -X POST http://localhost:4318/v1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "resourceMetrics": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "codex-test"}},
          {"key": "user.email", "value": {"stringValue": "test@example.com"}}
        ]
      },
      "scopeMetrics": [{
        "metrics": [{
          "name": "codex.test.counter",
          "unit": "1",
          "sum": {
            "dataPoints": [{
              "asInt": "42",
              "timeUnixNano": "'$(date +%s)000000000'"
            }],
            "aggregationTemporality": 2,
            "isMonotonic": true
          }
        }]
      }]
    }]
  }'
# Expected: HTTP 200 OK (or empty = success)

# Step 5: Verify in CloudWatch (wait 1-2 minutes)
aws cloudwatch list-metrics \
  --namespace "codex-test" \
  --region us-west-2

# Expected output:
# {
#   "Metrics": [
#     {
#       "Namespace": "codex-test",
#       "MetricName": "codex.test.counter",
#       ...
#     }
#   ]
# }

# Or check via console:
# https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#metricsV2:

# Step 6: Check collector logs (troubleshooting)
tail -f ~/.codex/otel/otelcol.log
# Look for:
# ✓ "Everything is ready. Begin running and processing data."
# ✓ "Exporting metrics" messages
# ✗ NO "SignatureDoesNotMatch" errors
# ✗ NO "AccessDenied" errors
```

**✅ Local Collector Success Criteria:**
- [ ] Collector starts without errors (PID shown)
- [ ] Status shows running with ~30-50MB memory
- [ ] Test metric returns HTTP 200
- [ ] Metric appears in CloudWatch within 2 minutes
- [ ] No authentication errors in logs
- [ ] Collector stops cleanly with `stop-collector.sh`

### Test 2: Run Real Codex Session (Client Metrics)

```bash
# Ensure local collector is running
~/.codex/otel/collector-status.sh

# Run Codex command
codex-gateway exec "What is 2+2? Answer in one word."

# Wait 1-2 minutes, then check CloudWatch metrics
aws cloudwatch list-metrics \
  --namespace "Codex" \
  --region us-west-2

# Expected metrics:
# - codex.turn.duration_ms
# - codex.turn.token_usage
# - codex.api_request
```

### Test 3: Central Collector (if Central or Hybrid mode)

```bash
# Step 1: Verify ECS collector is running
aws ecs describe-services \
  --cluster codex-gateway-otel-collector-cluster \
  --services codex-gateway-otel-collector-service \
  --region us-west-2 \
  --query 'services[0].{desired:desiredCount,running:runningCount,status:status}'

# Expected:
# {
#   "desired": 1,
#   "running": 1,
#   "status": "ACTIVE"
# }

# Step 2: Get collector endpoint
COLLECTOR_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name codex-gateway-otel-collector \
  --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`CollectorEndpoint`].OutputValue' \
  --output text)

echo "Collector endpoint: $COLLECTOR_ENDPOINT"

# Step 3: Test collector health
curl ${COLLECTOR_ENDPOINT}/
# Expected: HTTP 200 or 404 (ALB is responding)

# Step 4: Send test metric
curl -X POST "${COLLECTOR_ENDPOINT}/v1/metrics" \
  -H "Content-Type: application/json" \
  -H "x-user-email: test@example.com" \
  -H "x-user-id: testuser" \
  -d '{
    "resourceMetrics": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "codex-gateway-test"}}
        ]
      },
      "scopeMetrics": [{
        "metrics": [{
          "name": "codex.gateway.test.counter",
          "sum": {
            "dataPoints": [{
              "asInt": "100",
              "timeUnixNano": "'$(date +%s)000000000'"
            }],
            "aggregationTemporality": 2,
            "isMonotonic": true
          }
        }]
      }]
    }]
  }'

# Expected: HTTP 200 OK

# Step 5: Verify in CloudWatch (wait 1-2 minutes)
aws cloudwatch list-metrics \
  --namespace "codex-gateway-test" \
  --region us-west-2

# Step 6: Check ECS collector logs
aws logs tail /ecs/codex-gateway-otel-collector-collector \
  --follow \
  --region us-west-2
# Press Ctrl+C to stop

# Look for:
# ✓ "Everything is ready. Begin running and processing data."
# ✓ Receiver endpoints: 0.0.0.0:4317, 0.0.0.0:4318
# ✓ "Exporting metrics" messages
# ✗ NO authentication errors
```

**✅ Central Collector Success Criteria:**
- [ ] ECS service shows desired=1, running=1
- [ ] Collector endpoint responds to health check
- [ ] Test metric returns HTTP 200
- [ ] Metric appears in CloudWatch within 2 minutes
- [ ] User attribution headers extracted (x-user-email, x-user-id)
- [ ] No errors in ECS logs

### Test 4: Gateway Metrics (Server-Side)

```bash
# If Central or Hybrid mode, LiteLLM gateway sends metrics automatically

# Run a Codex command
codex-gateway exec "What is 2+2?"

# Wait 1-2 minutes, then check for gateway metrics
aws cloudwatch list-metrics \
  --namespace "Codex" \
  --region us-west-2 \
  --metric-name "litellm.request.total"

# Or query with PromQL (in CloudWatch console):
# sum({__name__="litellm.request.total"})
```

### Test 5: View Unified Dashboard (Hybrid mode)

```bash
# Query client-side metrics
# PromQL: sum({__name__="codex.turn.duration_ms", source="client"})

# Query server-side metrics
# PromQL: sum({__name__="litellm.request.total", source="server"})

# Query by user
# PromQL: sum by (user_email) ({__name__=~"codex.*token.*"})

# Query cost by department (if headers propagated)
# PromQL: sum by (department) ({__name__=~".*token.*"})

# Open CloudWatch console:
open "https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#prometheus:query"
```

### Troubleshooting OTEL

#### Issue: Local collector won't start

**Symptom:** `start-collector.sh` fails or no PID shown

**Debug:**
```bash
# Check if port 4318 is available
lsof -i :4318
# If occupied, kill process: kill <PID>

# Check AWS credentials
aws sts get-caller-identity
# If expired: aws sso login --profile your-profile

# Check collector logs
tail -100 ~/.codex/otel/otelcol.log
# Look for error messages

# Test manually
cd ~/.codex/otel
./otelcol-local --config otel-config.yaml
# Press Ctrl+C to stop
```

#### Issue: Metrics not appearing in CloudWatch

**Checklist:**
1. Wait 1-2 minutes (metrics take time to propagate)
2. Check collector is running: `ps aux | grep otelcol`
3. Verify no authentication errors in logs
4. Confirm region matches: `us-west-2`
5. Check namespace is correct (service.name becomes namespace)

**Debug:**
```bash
# Check collector health
curl http://localhost:13133/
# Expected: HTTP 200

# Check CloudWatch endpoint is reachable
curl -v https://monitoring.us-west-2.amazonaws.com/
# Expected: HTTP 403 (endpoint exists, but needs auth)

# Verify IAM permissions
aws iam get-user --query 'User.Arn'
# Check your user/role has: monitoring:PutMetricData
```

#### Issue: ECS collector not starting

**Symptom:** ECS service shows desired=1, running=0

**Debug:**
```bash
# List tasks
TASK_ARN=$(aws ecs list-tasks \
  --cluster codex-gateway-otel-collector-cluster \
  --region us-west-2 \
  --query 'taskArns[0]' \
  --output text)

# Describe task to see failure reason
aws ecs describe-tasks \
  --cluster codex-gateway-otel-collector-cluster \
  --tasks $TASK_ARN \
  --region us-west-2 \
  --query 'tasks[0].{stopCode:stopCode,stopReason:stopReason,containers:containers[*].{name:name,reason:reason}}'

# Common issues:
# 1. SSM parameter not found → check OTelConfig exists
# 2. IAM permission denied → check TaskRole has monitoring:PutMetricData
# 3. ALB health check failing → check security groups allow ALB → Task
```

#### Issue: User attribution not working

**Symptom:** Metrics appear but no user.email dimension

**Fix for Local Collector:**
```bash
# Check config has user email
grep user.email ~/.codex/otel/otel-config.yaml
# Should show: value: "your-email@example.com"

# If placeholder, edit file:
sed -i '' 's/__USER_EMAIL__/your-email@example.com/g' ~/.codex/otel/otel-config.yaml

# Restart collector
~/.codex/otel/stop-collector.sh
~/.codex/otel/start-collector.sh
```

**Fix for Central Collector:**
```bash
# Check LiteLLM is sending user headers
# Look for x-user-email, x-user-id in request logs

# If missing, verify JWT middleware is extracting claims correctly
aws logs tail /ecs/litellm --follow --region us-west-2 --filter-pattern "jwt-middleware"
```

---

### Getting API Key - Two Options

Choose based on your organization's needs:

| Option | Setup Time | Best For |
|--------|-----------|----------|
| **Option A: Admin-Generated Keys** | 5 min | Small teams, quick start, simple workflow |
| **Option B: OIDC Self-Service** | 1-2 hours | Large teams, self-service, SSO integration |

---

#### Option A: Admin-Generated Key (Simplest)

```bash
# 1. Contact your platform team/admin
# 2. Request API key for Codex access
# 3. Admin generates key via LiteLLM UI:
#    - Logs into https://<gateway-url>/ui with master key
#    - Navigates to "API Keys" section
#    - Clicks "Create New Key"
#    - Fills in:
#        • Key Name: user-alice@company.com
#        • User ID: alice@company.com (optional)
#        • Max Budget: $50/month (optional)
#        • Models: gpt-4o, gpt-4o-mini (optional - leave blank for all)
#    - Shares key via secure channel (1Password, Vault, email)
#
# 4. Developer sets environment variable
export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx

# Add to shell profile for persistence:
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx' >> ~/.zshrc  # macOS
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx' >> ~/.bashrc # Linux

# 5. Restart your shell or source the profile
source ~/.zshrc  # macOS
source ~/.bashrc # Linux
```

**Key Management:**
- ✅ Keys do NOT expire by default (set once, use forever)
- ✅ Admin can optionally configure expiration when creating key
- ✅ Admin tracks usage per user via LiteLLM UI dashboard
- ✅ Admin can revoke keys when needed (employee leaves, compromised)

---

#### Option B: Self-Service OIDC Portal (Custom JWT Middleware)

**For large teams that need self-service key generation via corporate SSO.**

**→ [Complete OIDC Setup Guide](OIDC_SELF_SERVICE_SETUP.md)**

**Quick overview:**
- Developers authenticate via corporate IdP (Okta, Azure AD, Auth0)
- JWT middleware automatically creates/manages API keys
- Keys cached in DynamoDB (90-day TTL)
- Full audit trail in CloudWatch

**Setup:** Enable OIDC during `cxwb init`, build JWT middleware with `cxwb build-jwt`, then deploy.

See the [complete guide](OIDC_SELF_SERVICE_SETUP.md) for detailed setup steps, troubleshooting, and monitoring.

---

## What is codex-gateway?

**`codex-gateway` is an alias created by `install.sh` — it's a shortcut for calling Codex CLI with the right flags.**

```bash
# The alias looks like this:
alias codex-gateway='codex -c model_provider="litellm-gateway" -c model="openai.gpt-5.4"'

# Without the alias, you'd have to type:
codex -c 'model_provider="litellm-gateway"' -c 'model="openai.gpt-5.4"' exec "your prompt"

# With the alias, you just type:
codex-gateway exec "your prompt"
```

**What the alias does:**
1. Uses custom provider "litellm-gateway" (from `~/.codex/config.toml`)
2. Uses model "openai.gpt-5.4" (or whatever model was set during `cxwb init`)
3. Sends requests to: `http://<gateway-url>/v1`
4. Includes Authorization header with your API key

**Where it's created:** The `install.sh` script adds the alias to your shell profile (`~/.zshrc` or `~/.bashrc`), so it's available in all new terminal sessions after you run `source ~/.zshrc` (or restart your shell).

---

## Validation

### Test Gateway Health

```bash
# 1. Check gateway is responding
curl "$GATEWAY_URL/health"

# Expected: {"status":"healthy"}

# 2. Test OpenAI compatibility
curl "$GATEWAY_URL/v1/models" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"

# Expected: List of configured models

# 3. Test Bedrock integration
curl "$GATEWAY_URL/v1/chat/completions" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai.gpt-5.4",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'

# Expected: JSON response with completion
```

### Test Quota Enforcement

```bash
# 1. Create test key with low budget
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "test-quota",
    "models": ["openai.gpt-5.4"],
    "max_budget": 0.10,
    "budget_duration": "1d"
  }'

# Save the returned key: TEST_KEY=sk-litellm-test-...

# 2. Make multiple requests until quota exceeded
for i in {1..20}; do
  curl "$GATEWAY_URL/v1/chat/completions" \
    -H "Authorization: Bearer $TEST_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai.gpt-5.4",
      "messages": [{"role": "user", "content": "Test '$i'"}],
      "max_tokens": 100
    }'
  sleep 1
done

# Expected: Eventually returns 429 Too Many Requests
# {"error": {"message": "Budget exceeded for key test-quota"}}
```

### Test Codex Integration

```bash
# 1. Check Codex config
cat ~/.codex/config.toml | grep -A5 "model_provider"

# Expected:
# model_provider = "openai"
# model = "openai.gpt-5.4"
# [openai]
# base_url = "https://<gateway-url>/v1"

# 2. Test Codex prompt
echo "Create a hello world function in Python" | codex

# Expected: Codex generates code via gateway
```

---

## Configure Quota Policies

### Per-User Budgets

```bash
# Create user-specific key
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "user-alice@company.com",
    "user_id": "alice@company.com",
    "models": ["openai.gpt-5.4"],
    "max_budget": 50.0,
    "budget_duration": "30d",
    "metadata": {"department": "engineering", "team": "frontend"}
  }'
```

### Per-Team Budgets

```bash
# Create team key with higher limits
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "team-platform",
    "team_id": "platform-team",
    "models": ["openai.gpt-5.4", "openai.gpt-oss-120b"],
    "max_budget": 500.0,
    "budget_duration": "30d",
    "tpm_limit": 100000,
    "rpm_limit": 1000,
    "metadata": {"cost_center": "CC-1234"}
  }'
```

### Rate Limits

```bash
# Set aggressive rate limits for new users
curl -X POST "$GATEWAY_URL/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "new-user-trial",
    "max_budget": 10.0,
    "budget_duration": "7d",
    "tpm_limit": 10000,
    "rpm_limit": 100,
    "duration": "7d"
  }'
```

### Model Routing

```bash
# Configure fallback model
curl -X POST "$GATEWAY_URL/model/new" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "openai.gpt-5.4",
    "litellm_params": {
      "model": "bedrock/openai.gpt-5.4",
      "aws_region_name": "us-west-2",
      "fallbacks": [
        {"model": "bedrock/openai.gpt-oss-120b"}
      ]
    }
  }'
```

---

## Monitoring Architecture Details

### Local Collector Components

```
~/.codex/otel/
├── otelcol-local              # Binary (~15MB)
├── otel-config.yaml           # Configuration
├── start-collector.sh         # Start script
├── stop-collector.sh          # Stop script
├── collector-status.sh        # Status check
├── otelcol.log                # Logs (created at runtime)
└── otelcol.pid                # Process ID (created at runtime)
```

**Configuration highlights:**
- **Receiver:** OTLP/HTTP on 127.0.0.1:4318 (localhost only)
- **Processor:** Adds user.email, user.id, source=client
- **Exporter:** Native OTLP to `https://monitoring.{region}.amazonaws.com`
- **Auth:** SigV4 using AWS SSO credentials
- **Health check:** HTTP endpoint on 127.0.0.1:13133

### ECS Collector Components

**CloudFormation Stack:** `{profile}-otel-collector`

```
Infrastructure:
├── ALB (internet-facing)
│   ├── HTTP listener (port 80) → redirect to HTTPS
│   └── HTTPS listener (port 443) → forward to tasks
├── Target Group (OTLP HTTP on port 4318)
├── ECS Service
│   ├── Cluster: {profile}-otel-collector-cluster
│   ├── Task: 1x Fargate (0.5 vCPU, 1GB RAM)
│   └── Image: aws-otel-collector:latest
├── SSM Parameter: {profile}-otel-collector-config
│   ├── Receiver: OTLP/HTTP on 0.0.0.0:4318
│   ├── Processor: Extracts x-user-email headers
│   ├── Exporter: Native OTLP to CloudWatch
│   └── Auth: SigV4 using ECS TaskRole
└── IAM Roles
    ├── TaskExecutionRole: ECR pull, SSM read, CloudWatch Logs
    └── TaskRole: cloudwatch:PutMetricData, monitoring:PutMetricData
```

### Metrics Reference

#### Client-Side Metrics (Local Collector)

| Metric | Type | Description | Dimensions |
|--------|------|-------------|------------|
| `codex.turn.duration_ms` | Histogram | E2E latency per turn | user.email, model, session_source |
| `codex.turn.token_usage` | Counter | Tokens by type | token_type, user.email, model |
| `codex.api_request` | Counter | API calls | status, user.email |

**Resource attributes:**
- `source=client` (client-side)
- `collector.type=local`
- `user.email`, `user.id`

#### Server-Side Metrics (Central Collector)

| Metric | Type | Description | Dimensions |
|--------|------|-------------|------------|
| `litellm.request.total` | Counter | Total API requests | user.email, department, endpoint, status |
| `litellm.bedrock.tokens` | Counter | Bedrock token usage | token_type, model, user.email |
| `litellm.request.duration` | Histogram | Gateway latency | endpoint, status |

**Resource attributes:**
- `source=server` (server-side)
- `aws.account_id`
- `user.email`, `department`, `team.id` (from headers)

### PromQL Query Examples

```promql
# Total tokens by user (all sources)
sum by (user_email) ({__name__=~".*token.*"})

# API requests by status code
sum by (status) ({__name__="codex.api_request"})

# Average turn duration by user
avg by (user_email) ({__name__="codex.turn.duration_ms"})

# Client vs Server latency comparison
avg({__name__="codex.turn.duration_ms", source="client"})
  - avg({__name__="litellm.request.duration", source="server"})

# Token usage by department
sum by (department) ({__name__=~".*token.*"})

# Error rate by user
sum by (user_email) ({__name__=~".*request.*", status=~"4..|5.."})
  / sum by (user_email) ({__name__=~".*request.*"})
```

### Cost Tracking

**Local Collector (per developer):**
- Binary download: $0 (one-time)
- Collector process: $0 (uses local CPU/memory)
- CloudWatch metrics: ~$0.30/month (1000 metrics/day × $0.01 per 1000)
- Network egress: ~$0.10/month (compressed OTLP)
- **Total per developer:** ~$0.40/month

**ECS Central Collector:**
- ECS Fargate: $14.40/month (0.5 vCPU + 1GB RAM, 24×7)
- ALB: $16.20/month ($0.0225/hr base)
- CloudWatch metrics: ~$0.30/month
- CloudWatch Logs: $0.50/month (7-day retention)
- **Total:** ~$31/month

**Hybrid (both):**
- Local collectors (50 devs): $20/month
- ECS collector: $31/month
- **Total for 50 developers:** ~$51/month (~$1/dev)

### IAM Permissions Required

**For Developers (Local Collector):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "monitoring:PutMetricData",
      "Resource": "*"
    }
  ]
}
```

**For ECS Collector (TaskRole):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "monitoring:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### Manual OTEL Collector Binary Download

If you prefer to download the binary manually or need a specific version:

```bash
# From repo root
cd guidance-for-codex-on-amazon-bedrock/deployment/scripts

# Download for your platform
./build-local-collector.sh --platform darwin-arm64
# Options: darwin-arm64, darwin-amd64, linux-amd64, windows-amd64

# Download specific version
ADOT_VERSION=v0.40.0 ./build-local-collector.sh --platform darwin-arm64

# Download all platforms
./build-local-collector.sh --all

# Binary saved to: ../binaries/otelcol-local-<platform>
```

---

## Troubleshooting

### Issue: Gateway returns 500 "Database connection failed"

**Cause:** RDS database not accessible from ECS tasks

**Fix:**
```bash
# Check security group allows ECS → RDS traffic
aws ec2 describe-security-groups \
  --filters "Name=tag:aws:cloudformation:stack-name,Values=codex-gateway" \
  --query 'SecurityGroups[*].[GroupId,GroupName]'

# Verify RDS endpoint resolves
nslookup <rds-endpoint>

# Check ECS task logs
aws logs tail /ecs/codex-gateway --follow
```

### Issue: Gateway returns 403 "AccessDeniedException" when calling Bedrock

**Cause:** ECS task role missing Bedrock permissions

**Fix:**
```bash
# Get task role ARN
TASK_ROLE=$(aws cloudformation describe-stacks \
  --stack-name codex-gateway \
  --query 'Stacks[0].Outputs[?OutputKey==`TaskRoleArn`].OutputValue' \
  --output text)

# Verify policy attached
aws iam list-attached-role-policies --role-name <role-name>

# Manually attach if missing
aws iam attach-role-policy \
  --role-name <role-name> \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

### Issue: Self-service key generation fails with OIDC error

**Cause:** OIDC redirect URI mismatch

**Fix:**
1. Check IdP application settings
2. Verify redirect URI: `https://<gateway-url>/sso/callback`
3. Update CloudFormation parameter `OIDCRedirectURI` if ALB URL changed

### Issue 4: Docker Not Running During Build

**Symptom:**
```bash
uv run cxwb build --profile <profile-name>
# Error: failed to connect to docker API
```

**Cause:** Docker Desktop not running

**Fix:** Open Docker Desktop, wait for it to start, verify with `docker ps`, retry build

### Issue 5: ALB Connection Refused / Listener Deleted by AWS

**Symptom:** `curl: (7) Failed to connect` or connection timeout

**Cause:** AWS security scan auto-deleted publicly accessible ALB listener (`0.0.0.0/0`)

**Fix:** Restrict to your IP or corporate CIDR, then redeploy:
```bash
# Get your IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Update profile
cd ~/.cxwb/profiles
jq --arg ip "$MY_IP/32" '.allowed_cidr = $ip' <profile>.json > tmp.json && mv tmp.json <profile>.json

# Redeploy
cd guidance-for-codex-on-amazon-bedrock/source
uv run cxwb destroy --profile <profile> --yes
uv run cxwb deploy --profile <profile>
```

### Issue 6: Model Identifier Invalid

**Symptom:** `BedrockException - model identifier is invalid`

**Cause:** LiteLLM config uses wrong Bedrock model ID

**Fix:**
```bash
# Check available models
aws bedrock list-foundation-models --region us-west-2 \
  --query 'modelSummaries[?contains(modelId,`openai`)].{ModelId:modelId,Name:modelName}'

# Update deployment/litellm/litellm_config.yaml with correct IDs
# Rebuild and redeploy
uv run cxwb build && uv run cxwb deploy
```

### Issue 7: Authentication Error - Malformed API Key

**Symptom:** `Malformed API Key - Ensure Key has Bearer prefix`

**Cause:** Typo in environment variable - `OPEN_API_KEY` instead of `OPENAI_API_KEY`

**Fix:** `export OPENAI_API_KEY="sk-..."` (correct spelling)

### Issue 8: ECS Tasks Crash - "exec format error"

**Symptom:** Tasks start then immediately stop

**Cause:** Image built for wrong architecture (ARM vs x86)

**Fix:** Rebuild with multi-arch (default): `uv run cxwb build --profile <profile>`

### Issue 9: IP Changed, Gateway Unreachable

**Symptom:** Was working, now connection refused

**Cause:** Your IP changed, security group has old IP

**Fix:** Update security group or redeploy with new IP (see Issue 5)

### Issue 10: OIDC JWT Validation Fails

**Symptom:** Self-service portal or API call returns `{"error": "Invalid JWT token: ..."}`

**Cause:** JWT validation failed - could be JWKS URL unreachable, expired token, or claim mismatch

**Fix:**
```bash
# 1. Verify JWKS URL is accessible from ECS tasks
curl https://your-tenant.okta.com/.well-known/jwks.json

# 2. Decode JWT to inspect claims (use jwt.io or command line)
echo "$JWT_TOKEN" | cut -d. -f2 | base64 -d | jq

# Required claims:
# - sub (user ID) - REQUIRED
# - email (user email) - optional but recommended
# - groups (array) - optional

# 3. Check JWT middleware environment variables match IdP
aws ecs describe-task-definition \
  --task-definition codex-litellm-gateway-task \
  --query 'taskDefinition.containerDefinitions[?name==`jwt-middleware`].environment' \
  --region us-west-2

# Should show:
# - JWKS_URL: your IdP's JWKS endpoint
# - JWT_AUDIENCE: (if set, must match token's "aud" claim)
# - JWT_ISSUER: (if set, must match token's "iss" claim)

# 4. Check JWT middleware logs
aws logs tail /ecs/litellm --follow --region us-west-2 --filter-pattern "jwt-middleware"

# 5. Test JWT middleware directly
curl https://<gateway-url>/api/my-key \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -v

# If JWT is valid but key creation fails, check LiteLLM master key in Secrets Manager
```

### General Debugging Tips

**Network Access Issues:**
- Enterprise customers should use corporate network CIDR, not `0.0.0.0/0`
- AWS security scans auto-delete public listeners without WAF
- Update `AllowedCidr` in profile to corporate VPN range: `10.0.0.0/8`, `172.16.0.0/12`

**Multi-Architecture Docker Builds:**
- Default: builds for both ARM64 and x86_64 (works on all platforms)
- Single-arch: use `--no-multi-arch` flag for faster builds
- Cross-compilation: ARM Mac → x86 ECS uses QEMU (slower but works)

**Checking Service Health:**
```bash
# ECS service status
aws ecs describe-services --cluster codex-litellm-gateway-cluster \
  --services <service-name> --region us-west-2

# ALB target health
aws elbv2 describe-target-health --target-group-arn <tg-arn>

# CloudWatch logs
aws logs tail /ecs/litellm --follow --region us-west-2

# CloudFormation events
aws cloudformation describe-stack-events --stack-name codex-litellm-gateway \
  --region us-west-2 --max-items 10
```

---

## Cleanup

```bash
# 1. Delete CloudFormation stacks (in reverse order)
# Names match the wizard defaults; adjust if you used custom names in `cxwb init`.
aws cloudformation delete-stack --stack-name codex-litellm-gateway --region us-west-2
aws cloudformation delete-stack --stack-name codex-user-key-mapping --region us-west-2  # only if OIDC was enabled
aws cloudformation delete-stack --stack-name codex-networking --region us-west-2

# 2. Delete ECR repository
aws ecr delete-repository --repository-name codex-litellm-gateway --force --region us-west-2

# 3. Developers uninstall
./uninstall.sh
```

---

---

## Next Steps

- **Configure quota policies:** [Configure Quota Policies](#configure-quota-policies)
- **Configure telemetry:** [Telemetry](#telemetry)
- **Scale horizontally:** Add ECS task auto-scaling based on ALB metrics

---

## Support

- **Documentation:** [../QUICKSTART.md](../QUICKSTART.md)
- **Issues:** [GitHub Issues](https://github.com/aws-samples/guidance-for-codex-on-aws/issues)
- **LiteLLM docs:** [docs.litellm.ai](https://docs.litellm.ai)
