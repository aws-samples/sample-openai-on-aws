# Operate — Troubleshooting

Known failure modes across the deploy paths. Not exhaustive — add entries as new failure modes surface.

Symptoms are grouped by path. The **All paths** section applies
regardless of how you deployed.

---

## All paths

### `bedrock:InvokeModel` returns `AccessDeniedException`
- **Likely cause:** the caller's role has the Bedrock customer-managed
  policy attached, but the session doesn't match the trust policy's
  `aws:PrincipalArn` condition (`AWSReservedSSO_CodexBedrockUser_*`).
- **Fix:** verify `aws sts get-caller-identity` returns an ARN matching the
  permission-set name baked into the stack. If you renamed the permission
  set, redeploy `bedrock-auth-idc.yaml` with the new
  `PermissionSetNamePattern` parameter.

### Model ID returns 404 / `ResourceNotFoundException`
- **Likely cause:** the model ID in `~/.codex/config.toml` (or gateway
  `litellm_config.yaml`) is not available in the target region, or it is
  only served through the mantle endpoint (GPT-5.4 / GPT-5.5) and you are calling
  standard Converse, or vice versa.
- **Fix:** verify the model ID against the region matrix in
  [reference-regions.md](reference-regions.md). `openai.gpt-oss-120b-1:0`
  and similar models use standard Converse; `gpt-5.4` / `gpt-5.5` use the mantle
  endpoint.

### CloudTrail `userIdentity.principalId` shows assumed-role ARN, not SSO username
- **Expected.** The SSO username is in `userIdentity.onBehalfOf` or is
  parsed from the assumed-role session name (`...:<sso-username>`). CUR
  2.0's `line_item_iam_principal` column contains the full assumed-role
  ARN; join on the session-name suffix for per-user attribution.

---

## IdC path

### `aws sso login` opens browser but Codex still fails with expired creds
- **Likely cause:** The AWS SDK cached credentials expired before Codex could
  use them, or the SSO session was established but credentials weren't refreshed.
- **Fix:** Re-run the Codex prompt. If it persists, verify that `~/.aws/sso/cache/`
  contains a fresh JSON blob with a future `expiresAt` timestamp. Run
  `aws sts get-caller-identity --profile codex` to verify the credential chain works.

### Using `aws login` (console-login) profiles instead of `aws sso login`
- **Requires:** Codex ≥ 0.130.0 (PR #21623 enabled the SDK's
  `credentials-login` feature so `login_session` profiles resolve for Bedrock
  SigV4 signing).
- **Fix for older Codex:** upgrade to ≥ 0.130.0, or use an `aws sso login`
  profile.

### Codex CLI works in terminal but fails in desktop app / VS Code
- **Likely cause:** GUI apps on macOS launch with a minimal PATH and may not
  inherit shell environment variables or AWS credential chain.
- **Fix:** Ensure the AWS CLI is in a standard location (`/usr/local/bin/aws`
  or Homebrew paths). For GUI apps, verify that `~/.aws/config` uses SSO
  profiles correctly. Run `aws sts get-caller-identity --profile codex` from
  the terminal first to confirm credentials work before launching the GUI.

---

## Gateway (LiteLLM) path

### `cloudformation delete-stack` on `codex-litellm-gateway` hangs on RDS
- **Cause:** `DeletionProtection: true` on the RDS instance — CloudFormation cannot
  delete it until protection is cleared.
- **Fix:**
  ```bash
  aws rds modify-db-instance \
    --db-instance-identifier <id> \
    --no-deletion-protection --apply-immediately
  ```
  Then retry the stack delete.

### Gateway `POST /v1/responses` from outside the VPC times out
- **Cause:** ALB `AllowedCidr` defaults to `10.0.0.0/8` — by design, the
  gateway is internal-only.
- **Fix:** either deploy a bastion or connect through the corporate VPN, or
  temporarily add a `/32` ingress rule to the ALB security group, then remove it afterward.

### LiteLLM returns `400` with `"LLM Provider NOT provided"`
- **Cause:** the `model` parameter in the request does not match an alias
  in `litellm_config.yaml`.
- **Fix:** use one of the aliases defined in the embedded config (e.g.
  `gpt-oss-120b`), or rebuild the image after editing the config.

---

## Observability (OTel → CloudWatch)

### No metrics in `/aws/codex/metrics` after a Codex session
- **Checklist:**
  1. `curl <collector-alb>/v1/metrics` with an `x-user-id` header — does the
     synthetic POST arrive? If not, the collector or networking is broken.
  2. Verify that `~/.codex/config.toml` has an `[otel.exporter.otlp-http]`
     block with the *full* URL (Codex does not append `/v1/<signal>`).
  3. Verify Codex version ≥ 0.130 — older versions emit a different
     set of metric names than `otel-collector.yaml` declares.
  4. Wait at least 60 seconds — the batch processor flushes on an interval.

### Metrics land but `user.id` dimension is empty or shows incorrect value
- **Cause:** The `x-user-id` header in `~/.codex/config.toml` was not set or
  contains a placeholder value instead of the actual SSO identity.
- **Fix:** Update the `[otel.headers]` section in `~/.codex/config.toml` with
  the correct user identity. Get your SSO username with:
  `aws sts get-caller-identity --profile codex --query Arn --output text`
  (the SSO username follows the final `/` in the assumed-role ARN).

### Collector logs show `404` on `/v1/logs` or `/v1/traces`
- **Cause:** Codex emits logs and traces alongside metrics; the collector
  needs `nop`-exporter pipelines for those signals so clients do not retry
  on 4xx responses. If you see this, redeploy with the current
  `otel-collector.yaml`.
