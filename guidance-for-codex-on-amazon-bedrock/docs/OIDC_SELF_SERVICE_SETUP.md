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

## Setup: Enable OIDC

The canonical end-to-end deployment is in
[QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md). The OIDC-specific
steps below extract the JWT middleware path. Set `AWS_REGION`, `BEDROCK_REGION`,
and the ECR registry variables (`ECR_REGISTRY`, `LITELLM_IMAGE`, `JWT_IMAGE`)
once at the top of your shell session as shown in that guide.

**Step 1: Gather your IdP details**

Collect the following from your corporate IdP:

| Value | Description |
|-------|-------------|
| JWKS URL | `https://your-tenant.okta.com/.well-known/jwks.json` |
| JWT Audience | Client ID (optional — leave empty to skip audience validation) |
| JWT Issuer | Issuer URL (optional — leave empty to skip issuer validation) |

These map directly to the `JwksUrl`, `JwtAudience`, and `JwtIssuer` parameters
on the `litellm-ecs.yaml` stack.

**Step 2: Build and push the JWT middleware image to ECR**

```bash
export JWT_REPO=codex-jwt-middleware
export JWT_IMAGE_TAG=v1
export JWT_IMAGE="$ECR_REGISTRY/$JWT_REPO:$JWT_IMAGE_TAG"

aws ecr create-repository \
  --repository-name "$JWT_REPO" \
  --region "$AWS_REGION" \
  --image-scanning-configuration scanOnPush=true \
  || echo "Repository already exists"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "$JWT_IMAGE" \
  --file deployment/litellm/jwt-middleware/Dockerfile \
  --push \
  deployment/litellm/jwt-middleware
```

**Step 3: Build and push the LiteLLM image**

Follow Step 2 of [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md#step-2-build-and-push-the-litellm-image)
to build and push `$LITELLM_IMAGE`.

**Step 4: Deploy the user-key-mapping DynamoDB stack**

```bash
aws cloudformation deploy \
  --stack-name codex-user-key-mapping \
  --template-file deployment/litellm/ecs/user-key-mapping.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides TableName=codex-user-keys
```

**Step 5: Deploy the LiteLLM gateway with JWT middleware enabled**

```bash
export GATEWAY_STACK=codex-litellm-gateway
export LITELLM_MASTER_KEY="sk-litellm-$(openssl rand -hex 24)"
export DB_PASSWORD="$(openssl rand -base64 24 | tr -d '/+=')"

aws cloudformation deploy \
  --stack-name "$GATEWAY_STACK" \
  --template-file deployment/litellm/ecs/litellm-ecs.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides \
      NetworkingStackName=codex-networking \
      LiteLLMMasterKey="$LITELLM_MASTER_KEY" \
      DBUsername=litellm \
      DBPassword="$DB_PASSWORD" \
      AwsRegion="$BEDROCK_REGION" \
      LiteLLMImage="$LITELLM_IMAGE" \
      AlbCertificateArn="$ALB_CERTIFICATE_ARN" \
      AlbDomainName="$GATEWAY_DOMAIN_NAME" \
      EnableJwtMiddleware=true \
      JwtMiddlewareImage="$JWT_IMAGE" \
      JwksUrl="https://your-tenant.okta.com/.well-known/jwks.json" \
      JwtAudience="your-client-id" \
      JwtIssuer="https://your-tenant.okta.com" \
      UserKeyMappingStackName=codex-user-key-mapping
```

The stack output `GatewayEndpoint` is your gateway base URL; the self-service
portal is served at `<GatewayEndpoint>/api/my-key`.

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
#   "api_key": "sk-litellm-xxxxxxxxxxxxx",  # gitleaks:allow
#   "user_id": "user@company.com",
#   "email": "user@company.com"
# }
```

**Method 3: Direct Usage (Transparent)**

```bash
# Developers can use JWT tokens directly for API calls
# (middleware auto-creates key on first request)

export JWT_TOKEN="eyJhbGc..."  # gitleaks:allow  # nosemgrep: generic.secrets.gitleaks.generic-api-key

curl https://<gateway-url>/v1/responses \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.5",
    "input": "Hello!"
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
export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx  # gitleaks:allow

# Add to shell profile for persistence:
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx  # gitleaks:allow' >> ~/.zshrc  # macOS
echo 'export OPENAI_API_KEY=sk-litellm-xxxxxxxxxxxxx  # gitleaks:allow' >> ~/.bashrc # Linux

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
