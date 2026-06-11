# Decide

Two deployment patterns, in recommended order. Choose the first one your organization can run.

> **Decision rule:** If you can run IAM Identity Center, use Native AWS Access.
> If you need hard per-user budgets or rate limiting, use LLM Gateway.

## Pattern Comparison

| Capability | Native AWS Access | LLM Gateway |
|------------|-------------------|------------------|
| **Authentication** | SAML → IdC | OIDC → Gateway |
| **IAM Identity Center Required?** | ✅ Yes | ❌ No |
| **Path to Bedrock** | Codex → Bedrock (native AWS SDK) | Codex → Gateway → Bedrock |
| **Developer Command** | `aws sso login` | `export OPENAI_API_KEY=...` |
| **Per-user CloudTrail Audit** | ✅ Native | ✅ Gateway logs |
| **Soft Alerts (CloudWatch)** | Optional | Optional |
| **Hard Budget Limits** | ❌ No | Optional |
| **Per-team Quotas** | ❌ No | Optional |
| **Rate Limiting (RPM/TPM)** | ❌ No | Optional |
| **Model Routing/Fallback** | ❌ No | ✅ Yes |
| **Setup Time** | 5-60 min | 15 min |
| **Infra Cost** | Free (AWS control plane) | ~$100-150/mo |

---

---

## Prerequisite checklist — Native AWS Access (IAM Identity Center)

Run this path if **all** of the following are true:

- [ ] AWS Organizations is enabled (or you can enable it).
- [ ] Your IdP supports SAML 2.0 + SCIM 2.0 (EntraID, Okta, Ping, JumpCloud,
      Google Workspace, CyberArk, OneLogin).
- [ ] You can distribute AWS CLI v2 to developers (winget / MSI / Homebrew /
      MDM).
- [ ] Amazon Bedrock is activated in at least one region you plan to use
      (see [reference-regions.md](reference-regions.md) for the model × region matrix).
- [ ] Per-user *attribution* in CloudTrail/CUR is sufficient — you do **not**
      require hard per-user token or cost cutoffs.

If all five apply, proceed to [Deploy — IAM Identity Center](deploy-identity-center.md) or [QUICKSTART_NATIVE_AWS_ACCESS.md](QUICKSTART_NATIVE_AWS_ACCESS.md).

## Prerequisite checklist — LLM Gateway

Run this path if IdC is not available **or** you need centralized
enforcement. All of the following must apply:

- [ ] IdC is not achievable, **or** you require one of the following: hard per-user token or cost
      budgets with automatic cutoff behind a single endpoint; reuse of an existing
      platform-team gateway.
- [ ] You have a container runtime you can operate (ECS Fargate, EKS, or
      equivalent) plus ALB and Postgres. Reference LiteLLM footprint is
      ~$90–150/mo + 0.1–0.25 FTE of ongoing ops.
- [ ] You have an OIDC IdP that can issue JWTs to developer machines (for
      client → gateway auth).
- [ ] You accept Codex running as a generic OpenAI provider (`model_provider
      = "openai"` + custom `base_url`), bypassing the native `amazon-bedrock`
      code path.
- [ ] Amazon Bedrock is activated in the region the gateway task role will
      call (see [reference-regions.md](reference-regions.md)).

**Reference implementation:** this repository ships LiteLLM under
`deployment/litellm/` as a working example. The pattern applies equally to
other OpenAI-compatible gateways — **Portkey**, **Bifrost**, **Kong AI Gateway**,
**Helicone**, the **AWS Bedrock Gateway** sample, or a custom FastAPI shim.
Choose whichever matches your organization's operational posture.

*(Canonical deploy doc: [QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md).)*

---

## Why this order

**Native AWS Access (IdC) is recommended first because:**

1. **Enterprise audiences need centralized cost and usage attribution with
   scalable distribution.** That eliminates the static Bedrock API key as a
   ranked option — Bedrock's own documentation describes it as a pilot/POC
   mechanism, not an enterprise path.
2. **IdC delivers all three from a single identity plane.** SSO user name in
   CloudTrail → CUR attribution; the same identity stamped into OTel as
   `user.id` → CloudWatch dashboards; signed AWS CLI v2 distribution →
   no SmartScreen or Gatekeeper friction.
3. **Native Codex integration.** Codex natively speaks SigV4 to Bedrock via the AWS SDK credential chain.

**LLM Gateway provides additional value for:**

1. **Hard enforcement.** The gateway retains real value for *enforcement* (hard per-user budgets, rate limiting, central policy).
2. **Organizations without IdC.** Gateway with OIDC is faster to set up than IdC + SAML federation.

**Trade-offs:**

- Pointing Codex at a gateway requires `model_provider = "openai"` with a custom `base_url`,
  bypassing the native `amazon-bedrock` code path.
- Gateway adds operational overhead (~$100-150/mo + 0.1-0.25 FTE).

## Open questions that may shift the pick

- **Session duration vs. long Codex runs.** The 8-hour default IdC session can
  interrupt multi-hour agent runs. Raise the permission-set session duration or
  accept `aws sso login` re-authentication as expected UX.
- **GovCloud parity.** Whether IdC-in-GovCloud meets the FedRAMP alignment
  some customers require is not yet confirmed.
