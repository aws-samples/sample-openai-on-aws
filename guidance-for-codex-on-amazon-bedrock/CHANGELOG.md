# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- Updated Codex monitoring guidance to use CloudWatch native OTLP as the default
  collector export path, with EMF logs enabled only for optional analytics.
- Reworked the Codex OTEL dashboard to use native CloudWatch PromQL widgets
  over OTLP-ingested metrics instead of classic namespace searches and Logs
  widgets.
- Clarified monitoring docs, troubleshooting, and infrastructure reference
  around OTLP-first dashboards, `EnableAnalytics=true`, and the default `Codex`
  EMF namespace.

## [2.0.0] - 2026-05-23

### BREAKING CHANGES

The `cxwb` (Codex-with-Bedrock) wizard CLI and its generated developer
bundles have been removed. The repository is now CloudFormation-first:
infrastructure is deployed directly with `aws cloudformation deploy`, and
client-side configuration follows the official OpenAI Codex documentation
plus inline examples in this repo.

**Existing deployments are not affected.** CloudFormation stacks deployed
with 1.x continue to work without redeployment — the breaking changes
concern only the deployment workflow and developer-bundle generation, not
the templates themselves.

### Removed

- `source/cxwb/` — the `cxwb` Python CLI (init / deploy / distribute / refresh
  / cleanup commands) and its supporting modules (`aws.py`, `cli.py`,
  `paths.py`, `profile.py`, `commands/`).
- `source/pyproject.toml`, `source/uv.lock`, `source/README.md` — Python
  packaging for `cxwb` (no longer needed; `uv run cxwb …` workflows are gone).
- `source/cleanup-codex-openai.sh`, `source/refresh-codex-key.sh` — helper
  scripts that wrapped `cxwb` operations.
- `deployment/scripts/generate-codex-sso-config.sh` (447 lines) — generated
  developer bundles (`install.sh`, `config.toml` snippets, credential helper
  wiring) for the Native AWS Access pattern.
- `deployment/scripts/generate-codex-gateway-config.sh` (452 lines) —
  generated developer bundles for the LLM Gateway pattern.
- `~/.cxwb/profiles/` profile dependency in deployment scripts —
  `deploy-otel-stack.sh` and `deploy-cognito.sh` now accept CLI flags
  instead of reading per-profile JSON.
- **Local/Hybrid OTel monitoring modes** — `cxwb` supported three OTel
  modes: "central" (ECS collector), "local" (per-developer collector
  binary), and "hybrid" (both). Only the "central" mode is documented in
  the current quickstarts. The supporting assets (`deployment/scripts/build-local-collector.sh`,
  `deployment/templates/otel-local-config.yaml`, start/stop scripts) remain
  on disk but are not integrated into the developer configuration flow.
  Organizations requiring local-only monitoring (no ECS cost) should use the
  OpenTelemetry Collector directly following the [OpenTelemetry documentation](https://opentelemetry.io/docs/collector/).
  A future update may restore local/hybrid mode documentation.

### Added

- `deployment/infrastructure/README.md` — index of all 18 CloudFormation
  templates (Auth, Cognito building blocks, Distribution, Monitoring,
  Artifacts), parameter docs for the primary templates
  (`bedrock-auth-idc.yaml`, `networking.yaml`, `otel-collector.yaml`,
  `litellm-ecs.yaml`), deployment-order diagram, cross-stack
  export/import table, quick-start examples, and validation commands.
- Inline Codex CLI configuration examples in `QUICKSTART.md`,
  `docs/QUICKSTART_NATIVE_AWS_ACCESS.md`, and `docs/QUICKSTART_LLM_GATEWAY.md`
  (replacing the generated developer bundles).
- Links to the canonical OpenAI Codex documentation:
  - Configuration: <https://developers.openai.com/codex/config>
  - Advanced configuration: <https://developers.openai.com/codex/config-advanced>
  - Amazon Bedrock provider: <https://developers.openai.com/codex/providers/amazon-bedrock>

### Changed

- `QUICKSTART.md` — "Quick Setup with cxwb Wizard" section replaced with
  direct `aws cloudformation deploy` examples; decision-tree style preserved.
- `docs/QUICKSTART_NATIVE_AWS_ACCESS.md` — `cxwb init/deploy/distribute`
  workflow replaced with a single `aws cloudformation deploy` invocation
  for `bedrock-auth-idc.yaml`, plus inline IdC + AWS config examples.
- `docs/QUICKSTART_LLM_GATEWAY.md` — `cxwb` build/deploy flow replaced with
  Docker build, ECR push, and the four-stack chain (`networking` → optional
  `otel-collector` → `litellm-ecs` → optional `litellm-dashboard`) using
  AWS CLI.
- `docs/01-decide.md`, `docs/deploy-identity-center.md`,
  `docs/OIDC_SELF_SERVICE_SETUP.md` — `cxwb` references replaced with
  CloudFormation/AWS CLI equivalents and OpenAI doc links.
- `deployment/scripts/deploy-otel-stack.sh`,
  `deployment/scripts/deploy-cognito.sh` — accept CLI flags instead of
  `~/.cxwb/profiles/<name>.json`; include `--help` usage and
  pre-deployment validation.

### Migration Guide (1.x → 2.0)

If you have a 1.x deployment, follow these steps. **Do not redeploy your
stacks** — the templates have not changed and your existing infrastructure
keeps working.

1. **Snapshot your `cxwb` profile (one-time, before upgrading):**
   ```bash
   cat ~/.cxwb/profiles/<profile-name>.json
   ```
   Save this output. It records your stack names, regions, and parameters.
2. **List your existing stacks** so you can manage them later via AWS CLI:
   ```bash
   aws cloudformation list-stacks \
     --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
     --query 'StackSummaries[?starts_with(StackName, `codex`)].[StackName,StackStatus]' \
     --output table
   ```
3. **Pull current parameters** for any stack you may want to update later:
   ```bash
   aws cloudformation describe-stacks --stack-name <stack> \
     --query 'Stacks[0].Parameters'
   ```
4. **Upgrade the repo** to 2.0. No action is required for in-place stacks;
   they keep functioning under their existing IAM roles, ECS services,
   and dashboards.
5. **For future template updates**, deploy directly with the AWS CLI.
   Example (Native AWS Access via IAM Identity Center):
   ```bash
   aws cloudformation deploy \
     --template-file deployment/infrastructure/bedrock-auth-idc.yaml \
     --stack-name codex-bedrock-idc \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-west-2 \
     --parameter-overrides \
         AllowedBedrockRegions=us-east-1,us-west-2 \
         AllowedModelIdPattern='openai.gpt-*'
   ```
   See [`deployment/infrastructure/README.md`](deployment/infrastructure/README.md)
   for the full template index and parameter reference.
6. **Replace the generated developer bundle** with the inline configuration
   in [`docs/QUICKSTART_NATIVE_AWS_ACCESS.md`](docs/QUICKSTART_NATIVE_AWS_ACCESS.md)
   or [`docs/QUICKSTART_LLM_GATEWAY.md`](docs/QUICKSTART_LLM_GATEWAY.md), and
   the official OpenAI Codex configuration docs linked above.
7. **Optional cleanup:** once you have confirmed Codex still authenticates
   and Bedrock calls succeed, you can `rm -rf ~/.cxwb/` and uninstall the
   `cxwb` Python package from any environments where it was installed.

### Future Deployments

All deployments now go through `aws cloudformation deploy`. The two
supported patterns and their entry points:

| Pattern             | Entry template(s)                                                                       | Walkthrough                                            |
| ------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Native AWS Access   | `deployment/infrastructure/bedrock-auth-idc.yaml` (single stack)                        | [`docs/QUICKSTART_NATIVE_AWS_ACCESS.md`](docs/QUICKSTART_NATIVE_AWS_ACCESS.md) |
| LLM Gateway         | `deployment/infrastructure/networking.yaml` → `otel-collector.yaml` (optional) → `deployment/litellm/ecs/litellm-ecs.yaml` → `deployment/infrastructure/litellm-dashboard.yaml` (optional) | [`docs/QUICKSTART_LLM_GATEWAY.md`](docs/QUICKSTART_LLM_GATEWAY.md) |

For Codex CLI configuration on the client side, see the OpenAI docs linked
above and the inline `config.toml` examples in each quickstart.

## [1.0.0] - 2026-04-15

### Added
- Initial release of Guidance for Codex with Amazon Bedrock
- `cxwb` wizard covering four deployment shapes: IdC deploy / IdC BYO / LiteLLM Gateway deploy / Gateway BYO
- Gateway developer bundle generator (`generate-codex-gateway-config.sh`) — bundles never contain keys; developers self-serve via the gateway's SSO endpoint
- Enterprise deployment patterns for OpenAI Codex CLI with Amazon Bedrock
- OIDC-based identity provider integration (Auth0, Azure AD, Cognito, Okta)
- Cross-region inference support via Amazon Bedrock CRIS profiles
- Monitoring dashboard with CloudWatch metrics and analytics pipeline
- Quota management per user and group
- Multi-platform credential process binaries (macOS arm64/intel, Linux, Windows)
- GovCloud (us-gov-west-1, us-gov-east-1) support
