# Option B: Self-Service OIDC Portal (Custom JWT Middleware)

**✅ NOW AVAILABLE** - Uses custom JWT middleware

**Architecture:**
```
Developer → Corporate IdP (Okta/Azure AD) → JWT Token
         ↓
JWT Middleware (validates JWT, manages user→key mapping)
         ↓
LiteLLM Gateway → Bedrock
```

**Benefits:**
- ✅ Developers self-serve (no admin bottleneck)
- ✅ Keys automatically linked to user identity
- ✅ Uses your existing corporate SSO (Okta, Azure AD, Auth0)
- ✅ Auto-caching in DynamoDB (90-day TTL)
- ✅ Audit trail (who generated what, when)

---

## Setup: Enable OIDC During Init

**Step 1: Configure OIDC in Profile**

```bash
cd guidance-for-codex-on-amazon-bedrock/source
uv run cxwb init

# Select: LiteLLM Gateway — deploy new
# When asked "Enable OIDC/SSO self-service?"
# → Choose "Yes - enable OIDC for self-service (requires IdP setup)"

# Provide your IdP details:
# - JWKS URL: https://your-tenant.okta.com/.well-known/jwks.json
# - JWT Audience: your-client-id (optional)
# - JWT Issuer: https://your-tenant.okta.com (optional)
```

**Step 2: Build JWT Middleware Image**

```bash
# Build and push JWT middleware Docker image to ECR
uv run cxwb build-jwt --profile <profile-name>

# This:
# - Builds image from deployment/litellm/jwt-middleware/
# - Creates ECR repository: codex-jwt-middleware
# - Pushes image to ECR
# - Updates profile with jwt_middleware_image_uri
```

**Step 3: Build LiteLLM Image (as usual)**

```bash
uv run cxwb build --profile <profile-name>
```

**Step 4: Deploy Infrastructure**

```bash
uv run cxwb deploy --profile <profile-name>

# This deploys (in order):
# 1. Networking stack (VPC, subnets)
# 2. OTel collector stack
# 3. DynamoDB table for user-key mapping
# 4. LiteLLM gateway with JWT middleware sidecar
#
# Output includes:
# GatewayEndpoint = http://<alb-url>/v1
# Self-service portal = http://<alb-url>/api/my-key
```

---

## Developer Experience: 3 Ways to Use OIDC

**Method 1: Self-Service Portal (Browser)**

```bash
# Developer opens portal in browser
open https://<gateway-url>/api/my-key

# 1. Browser redirects to corporate IdP (Okta/Azure AD)
# 2. Developer signs in with SSO credentials (work email + password + MFA)
# 3. IdP redirects back with JWT token
# 4. Middleware validates JWT, creates/fetches API key for user
# 5. API key displayed - developer copies it
```

**Method 2: Programmatic API Call**

```bash
# Get JWT token from your IdP (method varies by provider)
# For Okta example:
JWT_TOKEN=$(curl -X POST https://your-tenant.okta.com/oauth2/v1/token \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=openid email profile" \
  | jq -r '.access_token')

# Call API to get key
curl https://<gateway-url>/api/my-key \
  -H "Authorization: Bearer $JWT_TOKEN"

# Response:
# {
#   "api_key": "sk-litellm-xxxxxxxxxxxxx",
#   "user_id": "user@company.com",
#   "email": "user@company.com"
# }
```

**Method 3: Direct Usage (Transparent)**

```bash
# Developers can use JWT tokens directly for API calls
# (middleware auto-creates key on first request)

export JWT_TOKEN="eyJhbGc..."

curl https://<gateway-url>/v1/chat/completions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Middleware automatically:
# 1. Validates JWT signature and claims
# 2. Extracts user identity (sub, email)
# 3. Gets or creates API key for user (cached in DynamoDB)
# 4. Forwards to LiteLLM with API key
# 5. Streams response back
```

**Recommended for Most Users:** Method 1 (Self-Service Portal) - simple, visual, works for everyone.

---

## After Getting Key: Set Environment Variable

```bash
# Set for current shell
export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx

# Add to shell profile for persistence:
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx' >> ~/.zshrc  # macOS
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx' >> ~/.bashrc # Linux

# Restart your shell or source the profile
source ~/.zshrc  # macOS
source ~/.bashrc # Linux
```

---

## Key Management

**Caching:**
- User→key mappings cached in DynamoDB (90-day TTL)
- In-memory cache for JWT validation results
- First request: creates key + caches mapping (~200ms)
- Subsequent requests: cache hit (~20-50ms overhead)

**Revocation:**
- When user leaves company: disable in IdP → they can't authenticate
- Admin can manually revoke keys via LiteLLM UI if needed
- Keys automatically expire from cache after 90 days (re-generated on next use)

**Audit Trail:**
- All key creation logged to CloudWatch
- Includes: user_id, email, timestamp, source (jwt-middleware)
- Query logs: `aws logs tail /ecs/litellm --filter-pattern "Creating API key"`

---

## Troubleshooting OIDC

**Issue: JWT validation fails**

Symptom: `{"error": "Invalid JWT token: ..."}`

Causes:
1. JWKS URL incorrect or unreachable
2. JWT expired
3. JWT audience/issuer mismatch
4. JWT signed with wrong key

Fix:
```bash
# Verify JWKS URL is accessible
curl https://your-tenant.okta.com/.well-known/jwks.json

# Decode JWT to inspect claims (use jwt.io in browser or jq)
echo "$JWT_TOKEN" | cut -d. -f2 | base64 -d | jq

# Check audience and issuer match ECS environment variables
aws ecs describe-task-definition --task-definition <task-def-arn> \
  --query 'taskDefinition.containerDefinitions[?name==`jwt-middleware`].environment'
```

**Issue: API key creation fails**

Symptom: `{"error": "Key management failed: ..."}`

Causes:
1. LITELLM_MASTER_KEY invalid
2. LiteLLM container not responding
3. Network connectivity issues

Fix:
```bash
# Check LiteLLM is healthy
curl http://localhost:4000/health/liveliness

# Verify master key in Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id codex-litellm-gateway/litellm-master-key \
  --region us-west-2

# Check container logs
aws logs tail /ecs/litellm --follow --region us-west-2
```

**Issue: DynamoDB access denied**

Symptom: `Failed to cache API key in DynamoDB: ...`

Cause: ECS task role missing DynamoDB permissions

Fix:
```bash
# Check task role has DynamoDB policy
aws iam list-attached-role-policies --role-name <task-role-name>

# Should include policy with dynamodb:PutItem, dynamodb:GetItem
# If missing, redeploy stack (CloudFormation will add it)
```

---

## Monitoring OIDC Usage

**CloudWatch Logs:**
```bash
# View JWT middleware logs
aws logs tail /ecs/litellm --follow --region us-west-2 --filter-pattern "jwt-middleware"

# Common patterns:
# - "JWT validated for user" - successful authentication
# - "JWT validation failed" - invalid tokens
# - "Creating API key for user" - new key generation
# - "API key found in DynamoDB" - cache hit
```

**Metrics to Track:**
1. **Authentication success rate**: Valid vs invalid JWT tokens
2. **Key cache hit rate**: DynamoDB hits vs misses
3. **Key creation rate**: New keys per day
4. **Request latency**: Added latency from JWT validation (~20-50ms)

---

## Additional AWS Services

**Required for OIDC self-service (compared to admin-generated keys):**

| Service | Purpose |
|---------|---------|
| DynamoDB table | User→key mapping cache |
| ECS task (JWT middleware) | JWT validation (+0.25 vCPU, +512MB RAM) |
| ECR storage | Middleware container image (~100MB) |

---

## Alternative: Upgrade to LiteLLM Enterprise

If you need advanced features not in custom middleware:

| Feature | Custom JWT Middleware | LiteLLM Enterprise |
|---------|----------------------|-------------------|
| **Setup** | 1-2 hours | 1 hour |
| **OIDC/SSO** | ✅ Basic | ✅ Advanced (roles, RBAC) |
| **Key Management** | ✅ Auto-generation | ✅ Advanced policies |
| **Rate Limiting** | Use LiteLLM OSS features | ✅ Per-user/team |
| **Model Routing** | Use LiteLLM OSS features | ✅ Advanced routing |
| **Support** | Self-support | Enterprise support |

**Recommendation:** Start with custom middleware, upgrade to Enterprise later if you need vendor support or advanced RBAC.

---

## Learn More

**Detailed JWT Middleware Documentation:**
- Architecture: [deployment/litellm/jwt-middleware/README.md](../deployment/litellm/jwt-middleware/README.md)
- Configuration: Environment variables, DynamoDB setup, security
- IdP Setup Guides: Okta, Azure AD, Auth0 examples
- Advanced Topics: Redis caching, rate limiting, RBAC
