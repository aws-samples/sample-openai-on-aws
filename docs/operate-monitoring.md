# Operate — Monitoring & Cost Attribution

How to see who is using Codex, what they are spending, and when to alert.

Both deploy paths (IdC and Gateway) end in a user-scoped IAM session invoking
Bedrock. That single identity fans out into two authoritative signals —
**CloudTrail → CUR** for cost, **OTel → CloudWatch** for usage — plus an
optional cold-storage pipeline for deep historical queries.

## The identity chain

```
Corporate IdP (EntraID / Okta / …)
  └── SAML → IAM Identity Center
       └── aws sso login → temporary IAM credentials (assumed role)
            ├── bedrock:InvokeModel call
            │    └── CloudTrail userIdentity (SSO username)
            │         └── CUR 2.0 (line_item_iam_principal + cost-alloc tags)
            │              └── Per-user / per-team spend ← source of truth
            └── Codex OTel exporter (x-user-id header, install-time baked)
                 └── ADOT collector on ECS Fargate
                      └── CloudWatch EMF metrics (user.id dimension)
                           └── Per-user / per-team usage dashboard + quotas
```

Single identity, two dashboards. The Gateway path splits this into two
planes (JWT for attribution, task role for Bedrock) — see the gateway
caveat at the end.

This diagram is the canonical version. Other docs link here; do not copy.

---

## Three layers

| Layer | Purpose | Latency | Storage | Authority |
|---|---|---|---|---|
| **Live dashboards + quota alerts** | "What is happening now. Who is over budget." | ~60s | CloudWatch Metrics + Logs | Usage only |
| **Cost attribution** | "What each user or team cost this month." | ~24h | CUR 2.0 on S3 | Billing-grade |
| **Deep historical analytics** (optional) | Arbitrary SQL over months of token-level data. | ~5min | S3 Parquet + Athena | Usage only |

Select the layers you need. Most organizations run **live + cost**; add the
analytics pipeline only when CUR cannot answer the question (per-turn token
counts, TPM/RPM spikes, session-duration studies).

---

## Layer 1 — Live dashboards + quota alerts (CloudWatch)

### What's deployed

`deploy-otel-stack.sh` (used from the IdC and Gateway deploy docs) creates:

- **OTel collector** (ECS Fargate, `otel-collector.yaml`) behind an ALB.
  Receives OTLP/HTTP, maps the `x-user-id` header → `user.id` resource
  attribute, exports EMF to CloudWatch namespace `Codex`.
- **CloudWatch dashboard** `CodexOnBedrock` (`codex-otel-dashboard.yaml`) —
  per-user token spend estimate, API error rate, turn latency, session-source
  mix, active-developer leaderboard.

End users emit metrics automatically once their generated `~/.codex/config.toml`
ships with an `[otel]` block pointing at your collector (the generator embeds
this — see `deploy-identity-center.md` §5).

### Metrics Codex actually emits

Metrics emitted by Codex ≥ 0.130:

- `codex.api_request`, `codex.api_request.duration_ms` — HTTP call count + latency; dimension `status`.
- `codex.turn.e2e_duration_ms` — wall-clock per turn.
- `codex.turn.token_usage` — dimension `token_type` ∈ {input, output, cached_input, reasoning_output, total}.
- `codex.turn.tool.call`, `codex.turn.memory`, `codex.turn.network_proxy`.
- `codex.thread.started`, `codex.thread.skills.*`.
- `codex.shell_snapshot(.duration_ms)`, `codex.startup_prewarm.*`, `codex.plugins.startup_sync(.final)`, `codex.conversation.turn.count`.

Codex automatically stamps resource attributes: `service.name=codex_cli_rs`, `service.version`,
`app.version`, `model`, `originator`, `session_source`, `os`. These become
additional CloudWatch dimensions.

### Spend estimates on the live dashboard

The dashboard multiplies `codex.turn.token_usage` by the list price per 1M tokens
(defaults in `codex-otel-dashboard.yaml` — placeholder figures until GPT-5.4
pricing is published). **These are estimates.** The ground truth is CUR (Layer 2). If
numbers disagree, trust CUR.

### Quota alerts

Under IdC there is **no credential issuer to gate**: IdC issues session
credentials directly, and you cannot revoke them mid-session on token overage.

Recommended posture under IdC:

- **Soft alerts via CloudWatch alarms** on `codex.turn.token_usage` summed by
  `user.id` over a rolling window. Route to SNS for email or Slack.
- **Hard enforcement, if required, via the Gateway path.** LiteLLM's
  per-user and per-key budget controls sit in the request path and can actively
  deny requests.

---

## Layer 2 — Cost attribution (CloudTrail → CUR 2.0)

**Cleanest under IdC.** The Gateway path sees only the gateway's task role
in CloudTrail (see gateway caveat below).

### Per-user: built-in, no IdP changes

Every `bedrock:InvokeModel` call carries the SSO username in
`userIdentity.principalId`, which shows up in CUR 2.0 under
`line_item_iam_principal` as:

```
arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_CodexBedrockUser_…/alice@example.com
```

Enable it:

1. Billing → **Data Exports** → create or edit a Standard CUR 2.0 export.
2. Under **Additional export content**, enable **"Include caller identity
   (IAM principal) allocation data"**.
3. Query via Athena:

```sql
SELECT line_item_iam_principal, SUM(line_item_unblended_cost) AS usd
FROM cur2
WHERE line_item_product_code = 'AmazonBedrock'
  AND year = '2026' AND month = '5'
GROUP BY 1 ORDER BY usd DESC;
```

Cost Explorer does **not** expose `line_item_iam_principal` as a
filter or grouping dimension — you need Athena or QuickSight. If you want per-user
visibility *in Cost Explorer*, add session tags (next section).

### Per-team: IAM principal tags

All IdC users share the same role, so role-level tags provide team or department
rollups only — not per-user.

1. Tag the `CodexBedrockUser` role (or its permission-set-backed role) with
   `department`, `cost-center`, etc.
2. Billing → **Cost Allocation Tags** → filter by **IAM principal type**,
   select, **Activate**.
3. Tags take up to 24 hours to appear after the first tagged call, then up to 24 hours
   more to activate.

### Session tags for per-user Cost Explorer visibility

Optional. Needed only if you want per-user grouping in Cost Explorer (not just
Athena). Embed an `https://aws.amazon.com/tags` claim in the IdP's ID token —
formats vary by IdP (Auth0 uses a nested object; Okta and Entra use flattened per-key).
See the [AWS STS session-tags guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html)
for claim formats per IdP — this is an IdP-side customization, not
Codex-specific.

The role's trust policy must allow `sts:TagSession` or
`AssumeRoleWithWebIdentity` fails outright.

---

## Layer 3 — Deep historical analytics (optional)

When CUR and live dashboards do not answer the question — typically token-level
studies, TPM/RPM spike analysis, or multi-month session correlation — enable
the analytics pipeline:

- **Kinesis Firehose** streams `/aws/codex/metrics` CloudWatch Logs to S3 as
  Parquet, partitioned by `year/month/day/hour`.
- **Athena** with partition projection (no Glue crawler) queries the lake.
- **S3 lifecycle** transitions to Glacier after 90 days.

Cost: Firehose, S3, and Athena scans. For most organizations, CUR and live dashboards
suffice; enable this pipeline only when you have a specific query that requires it.
A CloudFormation template for this pipeline is not shipped in this repository —
build it when the need is concrete.

---

## LLM Gateway path caveat

If you route through an LLM Gateway, the identity chain splits:

- **CloudTrail** sees only the gateway's task role on every `InvokeModel`.
  `line_item_iam_principal` can no longer attribute cost to end users.
- **Cost attribution** moves into the gateway's own spend logs / metrics
  (e.g. LiteLLM's Postgres tables keyed by the JWT subject; Portkey's
  analytics; Kong's metrics plugin). Export to your BI layer for durable
  reporting.
- **Usage telemetry** is the gateway's responsibility on this path —
  configure the gateway's native OTel/Prometheus/spend callbacks, not the
  Codex-side OTel collector described in Layer 1.

This is the principal operational cost of choosing the gateway path. See
[QUICKSTART_LLM_GATEWAY.md](QUICKSTART_LLM_GATEWAY.md) for the LiteLLM
reference setup and its telemetry configuration.

---

## Verification checklist

After deploying the OTel stack and generating developer configs:

1. **Metric lands in CloudWatch.** `aws logs tail /aws/codex/metrics
   --region us-west-2 --follow` should show EMF events with `user.id`
   dimensions within ~60s of a Codex call.
2. **Dashboard renders per-user.** Open the `CodexOnBedrock` dashboard;
   "Estimated token spend per user" bar chart should show at least one
   user after a real session.
3. **CloudTrail logs the SSO username.** `aws cloudtrail lookup-events
   --lookup-attributes AttributeKey=EventName,AttributeValue=InvokeModel
   --region us-west-2` — `userIdentity.principalId` should contain the
   SSO email after the `/`.
4. **CUR principal column populates.** Up to 24h after the first invoke,
   `line_item_iam_principal` in your CUR 2.0 export should contain the
   same SSO email.

Steps 1–3 take seconds to minutes. Step 4 is the CUR latency — expect up to a day
before per-user spend appears in Athena.
