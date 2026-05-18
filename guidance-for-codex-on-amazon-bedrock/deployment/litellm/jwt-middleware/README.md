# JWT Middleware for LiteLLM Gateway

Custom JWT validation middleware that enables OIDC/SSO self-service API key generation **without requiring LiteLLM Enterprise license**.

## Overview

This middleware sits between your ALB and LiteLLM gateway, providing:
- ✅ JWT token validation from corporate IdP (Okta, Azure AD, Auth0, etc.)
- ✅ Automatic API key generation/management per user
- ✅ User-to-key mapping with DynamoDB caching
- ✅ Self-service portal for developers
- ✅ **No Enterprise license required**

## Architecture

```
Developer → Corporate IdP → JWT Token
         ↓
ALB (port 80) → JWT Middleware (port 8080)
         ↓
Validates JWT, extracts user identity
         ↓
Gets or creates LiteLLM API key for user
         ↓
Forwards request to LiteLLM (port 4000) with API key
         ↓
LiteLLM → Bedrock
```

## Components

1. **Flask Application** (`app.py`)
   - Validates JWT tokens using JWKS from IdP
   - Manages user-to-key mapping
   - Proxies requests to LiteLLM

2. **DynamoDB Table** (user-key-mapping.yaml)
   - Stores user_id → API key mappings
   - TTL: 90 days
   - Pay-per-request billing

3. **Self-Service Portal** (self-service-portal.html)
   - Web UI for developers to generate keys
   - OAuth2 redirect flow
   - One-click copy to clipboard

## Deployment

### Prerequisites

- Corporate IdP with OIDC support (Okta, Azure AD, etc.)
- JWKS URL from IdP
- AWS account with permissions for ECS, DynamoDB, ECR

### Step 1: Configure Profile with OIDC

```bash
cd guidance-for-codex-on-amazon-bedrock/source
uv run cxwb init

# When prompted:
# - Enable OIDC/SSO? → Yes
# - JWKS URL → https://your-tenant.okta.com/.well-known/jwks.json
# - JWT Audience → (optional, your client ID)
# - JWT Issuer → (optional, your IdP URL)
```

### Step 2: Build JWT Middleware Image

```bash
uv run cxwb build-jwt --profile <profile-name>

# This:
# - Builds Docker image from deployment/litellm/jwt-middleware/
# - Creates ECR repository: codex-jwt-middleware
# - Pushes image to ECR
# - Updates profile with jwt_middleware_image_uri
```

### Step 3: Build LiteLLM Image

```bash
uv run cxwb build --profile <profile-name>
```

### Step 4: Deploy Infrastructure

```bash
uv run cxwb deploy --profile <profile-name>

# This deploys (in order):
# 1. Networking stack (VPC, subnets)
# 2. OTel collector stack
# 3. DynamoDB user-key-mapping table
# 4. LiteLLM gateway with JWT middleware sidecar
```

## Developer Experience

### Option 1: Self-Service Portal (Browser)

```bash
# Developer opens portal in browser
open https://<gateway-url>/api/my-key

# 1. Browser redirects to corporate IdP (Okta/Azure AD)
# 2. Developer signs in with SSO credentials
# 3. IdP redirects back with JWT token
# 4. Portal calls /api/my-key with JWT
# 5. Middleware validates JWT, creates/fetches API key
# 6. API key displayed - developer copies it
```

### Option 2: API Call (Programmatic)

```bash
# Get JWT token from IdP (varies by provider)
JWT_TOKEN="eyJhbGc..."

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

### Option 3: Direct Usage (Transparent)

```bash
# Developer can also use JWT directly for API calls
# (middleware will auto-create key on first request)

export JWT_TOKEN="eyJhbGc..."

curl https://<gateway-url>/v1/chat/completions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"Hi"}]}'

# Middleware:
# 1. Validates JWT
# 2. Extracts user identity
# 3. Gets or creates API key for user
# 4. Forwards to LiteLLM with API key
# 5. Streams response back
```

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `JWKS_URL` | Yes | JWKS URL from IdP | `https://tenant.okta.com/.well-known/jwks.json` |
| `JWT_AUDIENCE` | No | Expected audience claim | `your-client-id` |
| `JWT_ISSUER` | No | Expected issuer claim | `https://tenant.okta.com` |
| `LITELLM_URL` | Yes | LiteLLM gateway URL | `http://localhost:4000` |
| `LITELLM_MASTER_KEY` | Yes | Master key for LiteLLM | `sk-xxx` (from Secrets Manager) |
| `DYNAMODB_TABLE` | Yes | DynamoDB table name | `codex-user-keys` |
| `AWS_REGION` | Yes | AWS region | `us-west-2` |

### JWT Claims Required

The middleware expects these claims in the JWT token:

- **`sub`** (required) - User ID
- **`email`** (optional) - User email
- **`groups`** (optional) - Array of group/team names

## Cost

**Additional AWS costs compared to standard LiteLLM deployment:**

| Service | Monthly Cost |
|---------|-------------|
| DynamoDB table | ~$1-5 (pay-per-request) |
| ECS task (JWT middleware) | ~$5 (+0.25 vCPU, +512MB) |
| ECR storage | ~$0.01 (+100MB) |
| **Total** | **~$6-10/month** |

**vs. LiteLLM Enterprise:** ~$500-2000+/month

## Monitoring

### CloudWatch Logs

```bash
# View JWT middleware logs
aws logs tail /ecs/litellm --follow --region us-west-2 --filter-pattern "jwt-middleware"

# Common log patterns to monitor:
# - "JWT validated for user" - successful authentication
# - "JWT validation failed" - invalid tokens
# - "Creating API key for user" - new key generation
# - "API key found in DynamoDB" - cache hit
```

### Metrics to Track

1. **Authentication success rate**: Valid vs invalid JWT tokens
2. **Key cache hit rate**: DynamoDB hits vs misses
3. **Key creation rate**: New keys per day
4. **Request latency**: Added latency from JWT validation (~20-50ms)

## Troubleshooting

### Issue: JWT validation fails

**Symptom:** `{"error": "Invalid JWT token: ..."}`

**Causes:**
1. JWKS_URL incorrect or unreachable
2. JWT expired
3. JWT audience/issuer mismatch
4. JWT signed with wrong key

**Fix:**
```bash
# Verify JWKS URL is accessible
curl https://your-tenant.okta.com/.well-known/jwks.json

# Check JWT claims match configuration
# Use jwt.io to decode and inspect your JWT token

# Verify audience and issuer in ECS task environment variables
aws ecs describe-task-definition --task-definition <task-def-arn> \
  --query 'taskDefinition.containerDefinitions[?name==`jwt-middleware`].environment'
```

### Issue: API key creation fails

**Symptom:** `{"error": "Key management failed: ..."}`

**Causes:**
1. LITELLM_MASTER_KEY invalid
2. LiteLLM container not responding
3. Network connectivity issues

**Fix:**
```bash
# Check LiteLLM is healthy
curl http://localhost:4000/health/liveliness

# Verify master key
aws secretsmanager get-secret-value \
  --secret-id codex-litellm-gateway/litellm-master-key \
  --region us-west-2

# Check container logs
aws logs tail /ecs/litellm --follow --region us-west-2
```

### Issue: DynamoDB access denied

**Symptom:** `Failed to cache API key in DynamoDB: ...`

**Cause:** ECS task role missing DynamoDB permissions

**Fix:**
```bash
# Check task role has DynamoDB policy
aws iam list-attached-role-policies --role-name <task-role-name>

# Should include DynamoDBAccess policy
# If missing, redeploy stack (CloudFormation will add it)
```

## Security Considerations

1. **JWT Signature Validation**: Always enabled via JWKS
2. **HTTPS**: Use ACM certificate on ALB (not shown in basic deployment)
3. **Network Security**: Restrict ALB security group to corporate network CIDR
4. **Key Storage**: API keys stored in encrypted DynamoDB table (KMS)
5. **Key Rotation**: Keys have 90-day TTL, auto-cleanup via DynamoDB TTL
6. **Audit Trail**: All key creation logged to CloudWatch

## Comparison: Custom Middleware vs LiteLLM Enterprise

| Feature | Custom Middleware | LiteLLM Enterprise |
|---------|-------------------|-------------------|
| **Cost** | ~$6-10/month | ~$500-2000+/month |
| **Setup Time** | ~1 day | ~1 day |
| **Maintenance** | Self-managed | Vendor-supported |
| **OIDC/SSO** | ✅ Basic | ✅ Advanced (roles, RBAC) |
| **Key Management** | ✅ Auto-generation | ✅ Advanced policies |
| **Audit Logging** | ✅ CloudWatch | ✅ Advanced audit trail |
| **Rate Limiting** | ❌ (use LiteLLM OSS) | ✅ Per-user/team |
| **Model Routing** | ❌ (use LiteLLM OSS) | ✅ Advanced routing |
| **Support** | Self-support | Enterprise support |

## Future Enhancements

- [ ] Support for SAML 2.0 (in addition to OIDC)
- [ ] Role-based access control (RBAC) from IdP groups
- [ ] Per-user/team rate limiting in middleware
- [ ] Key expiration notifications
- [ ] Admin dashboard for key management
- [ ] Redis caching for higher throughput
- [ ] Multi-region DynamoDB replication

## References

- [LiteLLM API Documentation](https://docs.litellm.ai/docs/proxy/token_auth)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [AWS Multi-Provider Gateway](https://github.com/aws-solutions-library-samples/guidance-for-multi-provider-generative-ai-gateway-on-aws) (inspiration)
