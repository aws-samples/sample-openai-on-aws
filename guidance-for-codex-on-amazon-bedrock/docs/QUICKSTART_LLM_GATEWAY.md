# Quick Start: LLM Gateway Pattern

Deploy Codex on Bedrock with an OpenAI-compatible LLM gateway for hard quota enforcement, rate limiting, and centralized policy control.

**Use this pattern if:**
- You need hard per-user/per-team budget limits (request blocking)
- You need rate limiting (RPM/TPM enforcement)
- You don't use AWS IAM Identity Center and don't want to set it up
- You need centralized model routing or automatic fallback

---

## Architecture

```
Corporate IdP (Okta/Azure) → OIDC/JWT → LLM Gateway → Amazon Bedrock
                                             ↓
                                    Quota enforcement
                                    Rate limiting (RPM/TPM)
                                    Cost attribution
                                    Model routing/fallback
```

**Key capabilities:**
- **Hard budget enforcement** — Gateway blocks requests when user/team hits spend limit
- **Rate limiting** — RPM (requests per minute) and TPM (tokens per minute) controls
- **Cost attribution** — Track spend by user, team, or department for chargeback through gateway telemetry and spend logs
- **Model routing** — Fallback logic, A/B testing, canary deployments
- **Centralized policy** — Update quotas without touching developer machines

---

## Choose Your Gateway

Any OpenAI-compatible gateway that can call Amazon Bedrock will work. Choose the one that matches your operational posture:

### AWS-Maintained Reference Implementation

| Gateway | Implementation Guide | Best For |
|---------|---------------------|----------|
| **LiteLLM** | [QUICKSTART_LLM_GATEWAY_LITELLM.md](QUICKSTART_LLM_GATEWAY_LITELLM.md) | Organizations new to LLM gateways, learning CloudFormation deployment patterns |

**Deployment:** ECS Fargate + Amazon RDS for PostgreSQL  
**Features:** Budget limits, RPM/TPM limits, model routing, team quotas, admin API  
**Setup time:** 15-20 minutes  
**Status:** Reference implementation — requires security hardening for production use (see implementation guide)  

---

### Other Gateway Options

Any OpenAI-compatible gateway that integrates with Amazon Bedrock can be used with this guidance. The gateway must meet the minimum requirements listed in the [Gateway Requirements](#gateway-requirements) section below.

---

## Gateway Requirements

Any gateway must meet these minimum requirements:

### Technical Requirements
- ✅ **OpenAI API compatibility** — implements `/v1/responses` for Codex and GPT-5.x workloads (optionally `/v1/chat/completions` for chat-style aliases)
- ✅ **Responses field fidelity** — preserves Codex/OpenAI request fields such as `reasoning.effort`, `text.verbosity`, `prompt_cache_key`, `previous_response_id`, and `phase` instead of silently dropping them
- ✅ **Bedrock integration** — can call Amazon Bedrock APIs (requires IAM role)
- ✅ **Gateway-managed upstream auth** — if proxying Bedrock Mantle, refreshes upstream bearer tokens inside the gateway rather than depending on a manually rotated static 12-hour token
- ✅ **Authentication** — supports API keys or JWT/OIDC tokens
- ✅ **AWS deployment** — runs on ECS, EKS, EC2, Lambda, or hybrid

### Operational Requirements (Recommended)
- ✅ **Quota enforcement** — per-user or per-team budget limits with automatic blocking
- ✅ **Rate limiting** — RPM and TPM controls
- ✅ **Admin API** — programmatic key generation and quota management
- ✅ **Telemetry** — metrics, logs, or traces for observability

---

## Deployment Pattern

All gateway implementations follow this general pattern:

### Phase 1: AWS Infrastructure (Common)

Deploy networking and optionally monitoring via CloudFormation:

```bash
# 1. Deploy VPC and subnets
aws cloudformation deploy \
  --stack-name codex-networking \
  --template-file deployment/infrastructure/networking.yaml \
  --region us-west-2
```

**(Optional) Deploy the OTel collector + CloudWatch dashboard for metrics.**
`otel-collector.yaml` creates IAM resources and requires several parameters
(`VpcId`, `SubnetIds`, `CustomDomainName`, `HostedZoneId`). Use the helper
script, which deploys networking + collector + dashboard with the right
capabilities and a single consistent metrics namespace:

```bash
deployment/scripts/deploy-otel-stack.sh \
  --region us-west-2 \
  --custom-domain otel.codex.example.com \
  --hosted-zone-id Z1234567890ABC
```

Run `deployment/scripts/deploy-otel-stack.sh --help` for HTTPS/JWT options.

### Phase 2: Gateway Deployment (Gateway-Specific)

Follow your chosen gateway's implementation guide:
- **LiteLLM**: Build Docker image → push to ECR → deploy ECS stack
- **Portkey**: Sign up → create virtual keys → configure Bedrock integration
- **Kong**: Deploy gateway → configure Bedrock upstream → enable plugins
- **Bifrost**: Deploy to ECS/EKS → configure config.yaml → point at Bedrock
- **Helicone**: Sign up → configure proxy → add Bedrock as provider

See the gateway-specific guide for exact steps.

### Phase 3: Developer Configuration (Common)

Once deployed, developers configure the user-level `~/.codex/config.toml` to
use the gateway. Your admin provides the gateway URL (for LiteLLM, it's the
`GatewayEndpoint` output from the gateway stack):

```toml
# ~/.codex/config.toml
model_provider = "my-gateway"
model = "gpt-5.5"  # Prefer the latest GPT-5 family model your gateway exposes

[model_providers.my-gateway]
name = "My LLM Gateway"
base_url = "<gateway-endpoint>"  # Paste the exact GatewayEndpoint value from your admin, including scheme and /v1
env_key = "OPENAI_API_KEY"
wire_api = "responses"  # Optional but explicit; custom providers default to Responses
```

Keep gateway provider settings in user-level `~/.codex/config.toml`; Codex
ignores `model_provider` and `model_providers` in project-local
`.codex/config.toml` files. If your gateway exposes different aliases, swap the
`model` string accordingly. If your gateway expects OpenAI authentication
instead of a gateway-specific API key, use `requires_openai_auth = true`
instead of `env_key`, per the Codex auth docs for custom providers.

```bash
# Set API key (get from gateway admin)
export OPENAI_API_KEY=<your-api-key>

# Test
codex exec "Hello world"
```

For advanced configuration, see [OpenAI Codex documentation](https://developers.openai.com/codex/config-advanced).

On this path, Bedrock CloudTrail and CUR attribute requests to the gateway IAM
role. For per-user or per-team reporting, rely on the gateway's own telemetry
and spend logs.

For enterprise rollout controls and Codex repo customization, use the official
OpenAI documentation:
- [Managed configuration (`requirements.toml`)](https://developers.openai.com/codex/enterprise/managed-configuration#admin-enforced-requirements-requirementstoml)
- [Sandbox and approvals](https://developers.openai.com/codex/concepts/sandboxing#configure-defaults)
- [AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [Customization](https://developers.openai.com/codex/concepts/customization#next-step)

---

## Bring Your Own Gateway

If your organization already operates an OpenAI-compatible gateway:

1. **Ensure gateway can call Bedrock** — Gateway's IAM role needs `bedrock:InvokeModel*` permissions
2. **Deploy common infrastructure** — Networking stack (optional if you have existing VPC)
3. **Point developers at your gateway** — Follow Phase 3 above with your gateway URL

No other AWS resources required.

---

## Next Steps

- **Pick your gateway** — Choose from the table above and follow that gateway's implementation guide
- **Compare with Native AWS Access** — See [QUICKSTART.md](../QUICKSTART.md) for pattern comparison
- **Monitor costs** — Most gateways provide built-in spend dashboards
- **Scale to more users** — Use OIDC self-service instead of admin-generated keys

---

## Support

- **Pattern documentation:** [QUICKSTART.md](../QUICKSTART.md)
- **Gateway-specific issues:** See your chosen gateway's implementation guide
- **General issues:** [GitHub Issues](https://github.com/aws-samples/sample-openai-on-aws/issues)
- **Codex configuration:** [OpenAI Codex docs](https://developers.openai.com/codex/config-advanced)

---

## Contributing a Gateway Implementation

Partners are welcome to contribute implementation guides for their gateways. See [CONTRIBUTING.md](../CONTRIBUTING.md) for the guide template and submission process.

**Requirements:**
- Gateway must deploy to AWS infrastructure (ECS, EKS, EC2, Lambda, or hybrid)
- Gateway must integrate with Amazon Bedrock
- Guide must include complete deployment steps, developer configuration, and troubleshooting
- Partner commits to maintaining the guide (responding to issues, updating for breaking changes)
