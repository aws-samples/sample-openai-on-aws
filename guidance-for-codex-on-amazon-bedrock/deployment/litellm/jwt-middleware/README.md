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

The canonical end-to-end gateway deploy is in
[`docs/QUICKSTART_LLM_GATEWAY.md`](../../../docs/QUICKSTART_LLM_GATEWAY.md);
the JWT-middleware-specific steps below extract the OIDC path. Set
`AWS_REGION` and the ECR registry variables (`ECR_REGISTRY`, `LITELLM_IMAGE`,
`JWT_IMAGE`) once at the top of your shell session.

### Step 1: Gather your IdP details

| Value | Description |
|-------|-------------|
| JWKS URL | `https://your-tenant.okta.com/.well-known/jwks.json` |
| JWT Audience | Client ID (optional — empty disables audience validation) |
| JWT Issuer | Issuer URL (optional — empty disables issuer validation) |

These map directly to the `JwksUrl`, `JwtAudience`, and `JwtIssuer` parameters
on `deployment/litellm/ecs/litellm-ecs.yaml`.

### Step 2: Build and push the JWT middleware image

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

### Step 3: Build and push the LiteLLM image

Follow Step 2 of [`QUICKSTART_LLM_GATEWAY.md`](../../../docs/QUICKSTART_LLM_GATEWAY.md#step-2-build-and-push-the-litellm-image)
to build and push `$LITELLM_IMAGE`.

### Step 4: Deploy the user-key-mapping DynamoDB stack

```bash
aws cloudformation deploy \
  --stack-name codex-user-key-mapping \
  --template-file deployment/litellm/ecs/user-key-mapping.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides TableName=codex-user-keys
```

### Step 5: Deploy the LiteLLM gateway with JWT middleware enabled

Deploy the networking stack first if not already in place
(`deployment/infrastructure/networking.yaml`), then:

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

Stack outputs include `GatewayEndpoint` (the gateway base URL); the
self-service portal is served at `<GatewayEndpoint>/api/my-key`.

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

curl https://<gateway-url>/v1/responses \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.5","input":"Hi"}'

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
2. **HTTPS**: ACM certificate on ALB is required by the ECS template
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
