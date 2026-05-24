# Guidance for Codex on Amazon Bedrock

Run [OpenAI Codex](https://github.com/openai/codex) against [Amazon Bedrock](https://aws.amazon.com/bedrock/) with enterprise-grade identity, optional quota enforcement, and optional observability.

This guidance provides two deployment patterns — choose the one that matches your organization's needs for budget enforcement.

---

## Choose Your Pattern

**Start with this decision tree:**

```
Question 1: Do you need HARD quota enforcement?
(Blocking requests when users hit limits, not just alerts)

├── YES → LLM Gateway
│         Why: IAM Identity Center (IdC) cannot block requests mid-session
│
└── NO → Question 2: Already use AWS IAM Identity Center (IdC)?

          ├── YES → Native AWS Access
          │         (Fastest: 5 min setup)
          │
          └── NO → Choose one:

                    Option A: Native AWS Access (Set up IdC + SAML)
                    • Pro: Native AWS integration
                    • Con: 30-60 min one-time setup

                    Option B: LLM Gateway (Use Gateway + OIDC)
                    • Pro: 15 min setup, no IdC needed
                    • Con: Additional infrastructure required
```

**Key Decision Factors:**

1. **Hard quotas require Gateway** — IdC issues credentials directly to users; AWS cannot revoke them mid-session
2. **If you have IdC already** — Native AWS Access is fastest (5 minutes)
3. **If you don't have IdC** — Choose between setting up IdC (native AWS integration) vs. Gateway (faster setup)

---

## Pattern Comparison

| Capability | Native AWS Access | LLM Gateway |
|------------|-------------------|------------------|
| **Authentication** | SAML → IdC | OIDC → Gateway |
| **IAM Identity Center Required?** | ✅ Yes | ❌ No |
| **Path to Bedrock** | Codex → Bedrock (native AWS SDK) | Codex → Gateway → Bedrock |
| **Developer Command** | `aws sso login` | `export OPENAI_API_KEY=...` |
| **Per-user CloudTrail Audit** | ✅ Native | ✅ Gateway logs |
| **Hard Budget Limits** | ❌ No | ✅ Provided by gateway |
| **Per-team Quotas** | ❌ No | ✅ Provided by gateway |
| **Rate Limiting (RPM/TPM)** | ❌ No | ✅ Provided by gateway |
| **Model Routing/Fallback** | ❌ No | ✅ Provided by gateway |
| **Setup Time** | 5-60 min | 15 min |

> **Quota enforcement is gateway-native, not extra AWS infrastructure.**
> Hard budgets, per-user / per-team quotas, and RPM/TPM rate limits are
> first-class features of every modern OpenAI-compatible gateway —
> [LiteLLM](https://docs.litellm.ai/docs/proxy/users),
> [Portkey](https://portkey.ai/docs/product/ai-gateway/budget-limits),
> [Kong AI Gateway](https://docs.konghq.com/hub/kong-inc/ai-rate-limiting-advanced/),
> and others all expose them via their admin APIs. You configure quotas
> against the gateway you deploy; you do **not** need a separate AWS
> Lambda or DynamoDB table for them. See
> [`docs/QUICKSTART_LLM_GATEWAY.md`](docs/QUICKSTART_LLM_GATEWAY.md#quota-enforcement)
> for concrete examples.

---

## Native AWS Access

> **"Codex on Bedrock with corporate SSO. No API keys, no custom binaries."**

### Who This Is For

- ✅ Organizations already using AWS IAM Identity Center
- ✅ Teams willing to set up SAML federation (30-60 min one-time setup)
- ✅ Environments where soft monitoring (alerts, not blocking) is sufficient
- ❌ NOT for: Hard budget enforcement or FinOps-controlled environments

### What Developers Experience

1. Run `aws sso login` — browser opens to corporate login page
2. Authenticate with existing credentials (Okta, Azure AD, Google, etc.)
3. Use Codex normally — credentials handled automatically by AWS CLI

**No custom executables. No credential helpers. No Python required.**

### Architecture

```
Corporate IdP (Okta/Azure) → SAML → IAM Identity Center → AWS credentials → Bedrock
                                                              ↓
                                                     CloudTrail attribution
```

### What Gets Deployed

- IAM role with Bedrock model invocation policy
- IAM Identity Center permission set (manual, one-time setup)

### Quick Start

**→ [docs/QUICKSTART_NATIVE_AWS_ACCESS.md](docs/QUICKSTART_NATIVE_AWS_ACCESS.md)**

**Prerequisites:**
- AWS account with IAM and CloudFormation permissions
- Amazon Bedrock activated in target regions
- Identity provider with SAML 2.0 support (Okta, Azure AD, etc.)
- AWS CLI v2 installed

**Deployment time:** 5 minutes (if IdC already set up) or 30-60 minutes (initial IdC setup)

---

## LLM Gateway

### Who This Is For

- ✅ Organizations that need hard per-user/per-team budget limits
- ✅ Teams where FinOps or platform team controls AI spend
- ✅ Environments requiring rate limiting (RPM/TPM enforcement)
- ✅ Organizations that don't use IdC and don't want to set it up

### What You Get

Capabilities depend on the gateway you deploy. Most OpenAI-compatible gateways provide:

- **OIDC / SSO authentication** — developers authenticate against your IdP
- **Per-user and per-team budgets** — gateway tracks spend and blocks when limits hit
- **Rate limiting** — requests per minute (RPM) and tokens per minute (TPM)
- **Model access policies** — control which teams can use which models
- **Cost attribution** — per user, team, or department for chargeback
- **Centralized policy management** — update limits without touching developer machines
- **Built-in telemetry** — gateways typically emit their own metrics, spend logs, and traces

### Architecture

```
Corporate IdP (Okta/Azure) → OIDC/JWT → LLM Gateway → Bedrock
                                              ↓
                                        Quota / rate limiting
                                        Cost attribution
                                        Model routing
```

### Gateway Choices

Any OpenAI-compatible gateway works — **[LiteLLM](https://www.litellm.ai/)**, **[Portkey](https://portkey.ai/)**, **[Bifrost](https://github.com/maximhq/bifrost)**, **[Kong AI Gateway](https://konghq.com/products/kong-ai-gateway)**, **[Helicone](https://helicone.ai/)**, the [AWS Bedrock Gateway sample](https://github.com/aws-samples/bedrock-access-gateway), or a custom FastAPI shim. Choose whichever matches your operational posture.

This repository ships **LiteLLM** as a reference implementation under `deployment/litellm/` — deployed on ECS Fargate via the CloudFormation templates in `deployment/litellm/ecs/`. If you bring your own gateway, deploy only the auth/networking stacks and point developers at your gateway URL.

### What Gets Deployed (Reference Implementation)

When you deploy the LiteLLM reference stacks:

- VPC with public/private subnets (or use existing VPC)
- ECS Fargate cluster running the gateway
- Application Load Balancer for ingress
- RDS Postgres for gateway state

### Quick Start

**→ [docs/QUICKSTART_LLM_GATEWAY.md](docs/QUICKSTART_LLM_GATEWAY.md)**

---

## Migration Notes

### Native AWS Access → LLM Gateway

**This is NOT a configuration change — it requires re-deployment.**

| Aspect | Changes Required |
|--------|-----------------|
| **Authentication** | Switch from SAML (IdC) to OIDC (Gateway) |
| **IdP Setup** | Create new OIDC app in your IdP |
| **Developer Workflow** | Change from `aws sso login` to API key |
| **Codex Config** | Change `model_provider` from `amazon-bedrock` to custom provider name (e.g., `litellm-gateway`) |
| **CloudTrail** | Attribution changes from per-user to gateway IAM role |

**Migration time:** 2-4 hours infrastructure + 1 hour per 10 developers for reconfiguration

**Best practice:** Test with pilot group (5-10 users) before org-wide rollout

---

## Supported Models

| Model ID | Notes |
|----------|-------|
| `openai.gpt-5.4` | **Recommended default.** Served via Bedrock Mantle. |
| `openai.gpt-oss-120b-1:0` | GPT-OSS 120B (Converse-compatible). |
| `openai.gpt-oss-20b-1:0` | GPT-OSS 20B (Converse-compatible). |
| `openai.gpt-oss-safeguard-120b` | Safeguard variant. |
| `openai.gpt-oss-safeguard-20b` | Safeguard variant. |

**Regions:** Available in `us-east-1`, `us-east-2`, `us-west-2`

Full region × model matrix: **[docs/reference-regions.md](docs/reference-regions.md)**

---

## Documentation Map

### Getting Started
- **[Choose Your Pattern](#choose-your-pattern)** — Decision tree (start here)
- **[docs/QUICKSTART_NATIVE_AWS_ACCESS.md](docs/QUICKSTART_NATIVE_AWS_ACCESS.md)** — Native AWS Access deployment
- **[docs/QUICKSTART_LLM_GATEWAY.md](docs/QUICKSTART_LLM_GATEWAY.md)** — LLM Gateway deployment

### Architecture & Deployment
- **[docs/01-decide.md](docs/01-decide.md)** — Detailed pattern comparison
- **[docs/deploy-identity-center.md](docs/deploy-identity-center.md)** — Native AWS Access technical guide

### Operations
- **[docs/operate-monitoring.md](docs/operate-monitoring.md)** — Monitoring and cost attribution
- **[docs/operate-troubleshooting.md](docs/operate-troubleshooting.md)** — Common issues and fixes

### Reference
- **[docs/reference-regions.md](docs/reference-regions.md)** — Supported regions and models

---

## Quick Setup with CloudFormation

Both patterns deploy directly with the AWS CLI against the templates under `deployment/infrastructure/` and `deployment/litellm/ecs/`. Follow the pattern-specific guide for end-to-end steps; the snippets below show the core commands.

### Native AWS Access

```bash
AWS_REGION=us-west-2

aws cloudformation deploy \
  --stack-name codex-bedrock-idc \
  --template-file deployment/infrastructure/bedrock-auth-idc.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION" \
  --parameter-overrides AllowedBedrockRegions="$AWS_REGION"
```

After the stack succeeds, create the `CodexBedrockUser` permission set in IAM Identity Center, then distribute the `~/.aws/config` and `~/.codex/config.toml` snippets shown in the [Developer Configuration](docs/QUICKSTART_NATIVE_AWS_ACCESS.md#developer-configuration) section of the full guide.

**Full guide:** [docs/QUICKSTART_NATIVE_AWS_ACCESS.md](docs/QUICKSTART_NATIVE_AWS_ACCESS.md)

### LLM Gateway (LiteLLM reference)

```bash
AWS_REGION=us-west-2

aws cloudformation deploy \
  --stack-name codex-networking \
  --template-file deployment/infrastructure/networking.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$AWS_REGION"

# Build and push the LiteLLM image to ECR first; see the full guide for the
# docker buildx commands and the LiteLLMImage / LiteLLMMasterKey / DBPassword
# values required by litellm-ecs.yaml.
aws cloudformation deploy \
  --stack-name codex-litellm-gateway \
  --template-file deployment/litellm/ecs/litellm-ecs.yaml \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
  --region "$AWS_REGION" \
  --parameter-overrides \
      NetworkingStackName=codex-networking \
      AwsRegion="$AWS_REGION" \
      LiteLLMImage="$LITELLM_IMAGE" \
      LiteLLMMasterKey="$LITELLM_MASTER_KEY" \
      DBPassword="$DB_PASSWORD"
```

After the gateway is reachable, distribute the `~/.codex/config.toml` snippet shown in the [Developer Configuration](docs/QUICKSTART_LLM_GATEWAY.md#developer-configuration) section of the full guide.

**Full guide:** [docs/QUICKSTART_LLM_GATEWAY.md](docs/QUICKSTART_LLM_GATEWAY.md)

**Supported deployment paths:**
- IdC + new stacks (Native AWS Access)
- IdC + existing stacks (Native AWS Access, BYO IdC)
- Gateway + new stacks (LLM Gateway)
- Gateway + existing stacks (LLM Gateway, BYO Gateway)

---

## Prerequisites

### For Administrators (Deployment)

**Software:**
- AWS CLI v2
- Git
- Docker (for LLM Gateway deployments — building the LiteLLM image)

**AWS Permissions:**
- CloudFormation stack creation
- IAM role and policy creation
- (Native AWS Access) IAM Identity Center management
- (LLM Gateway) ECS, VPC, ALB, RDS permissions

**Identity Provider:**
- (Native AWS Access) SAML 2.0 support (Okta, Azure AD, Auth0, Google)
- (LLM Gateway) OIDC support (Okta, Azure AD, Auth0, Cognito)

### For Developers (End Users)

**Native AWS Access:**
- AWS CLI v2 installed
- Web browser for SSO authentication
- No Python, Poetry, or Git required

**LLM Gateway:**
- Web browser for gateway authentication
- No AWS CLI required
- No Python, Poetry, or Git required

---

## Common Scenarios

### Scenario 1: Small Team, Already Use IdC
**Recommended:** Native AWS Access

- Setup time: 5 minutes
- Cost: $0
- Why: Fastest, leverages existing infrastructure

### Scenario 2: Mid-Size Team, Need Budget Control
**Recommended:** LLM Gateway

- Setup time: 15 minutes
- Cost: ~$100-150/month
- Why: Only way to enforce hard quotas

### Scenario 3: Startup, No IdC, No Budget for Gateway
**Recommended:** Native AWS Access (set up IdC)

- Setup time: 30-60 minutes (one-time)
- Cost: $0
- Why: Clean architecture, no ongoing costs

---

## Frequently Asked Questions

**Can I migrate from Native AWS Access to LLM Gateway later?**

Not without re-deployment. LLM Gateway uses different authentication (OIDC vs. SAML) and routing architecture (Gateway vs. direct Bedrock). If you anticipate needing quotas within 12 months, start with LLM Gateway.

**Do developers need to install anything?**

- Native AWS Access: AWS CLI v2 (if not already installed)
- LLM Gateway: Nothing (web-based authentication)

**Does LLM Gateway add latency?**

Yes, single-digit milliseconds (typically <10ms) as requests route through the gateway. Not noticeable for Codex use cases.

**What does the reference LLM Gateway cost to run?**

~$100-150/month for AWS infrastructure (ECS Fargate ~$70, ALB ~$20, Amazon RDS for PostgreSQL ~$30). Gateway licensing depends on the product you choose — review each vendor's pricing.

**Where do I report issues?**

→ [GitHub Issues](https://github.com/aws-samples/sample-openai-on-aws/issues)

---

## License

This guidance is licensed under [MIT No Attribution](LICENSE).

---

## Related Resources

- **[OpenAI Codex (GitHub)](https://github.com/openai/codex)** — Codex source and release notes
- **[OpenAI Codex CLI](https://developers.openai.com/codex/cli)** — Install, authenticate, and run Codex
- **[OpenAI Codex Advanced Configuration](https://developers.openai.com/codex/config-advanced)** — Custom providers, profiles, sandbox, OpenTelemetry
- **[Amazon Bedrock](https://aws.amazon.com/bedrock/)** — AWS managed AI service
- **[LiteLLM](https://www.litellm.ai/)** — Reference LLM gateway used in this guidance
- **[AWS IAM Identity Center](https://aws.amazon.com/iam/identity-center/)** — AWS SSO service
