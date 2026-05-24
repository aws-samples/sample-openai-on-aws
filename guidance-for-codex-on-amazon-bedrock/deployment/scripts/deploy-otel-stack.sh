#!/usr/bin/env bash
# Deploy the Codex-on-Bedrock OTel telemetry stack end-to-end:
#   1. networking.yaml           — VPC + public subnets for the collector
#   2. otel-collector.yaml       — ADOT collector on Fargate behind an ALB
#   3. codex-otel-dashboard.yaml — CloudWatch dashboard (usage + spend estimate)
#
# Emits the ALB endpoint so you can paste it into your Codex config.toml.
#
# Prereqs:
#   - AWS CLI v2 configured against the target account/region (env vars,
#     ~/.aws/credentials, or `aws sso login`)
#   - The Bedrock auth stack is a separate concern (bedrock-auth-idc.yaml)

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: deploy-otel-stack.sh [options]

Deploys three CloudFormation stacks (networking + collector + dashboard) to
provide central OpenTelemetry collection and a CloudWatch dashboard for
Codex-on-Bedrock usage.

Required: none (all options have sensible defaults).

Common options:
  --region REGION              AWS region (default: us-west-2)
  --aws-profile PROFILE        AWS named profile to use (optional;
                               otherwise uses the default credential chain)
  --stack-prefix PREFIX        Prefix for all three stacks (default: codex-otel)
  --dashboard-name NAME        CloudWatch dashboard name (default: CodexOnBedrock)
  --input-price N              USD per 1M input tokens (default: 0.15, placeholder)
  --output-price N             USD per 1M output tokens (default: 0.60, placeholder)
  --cached-input-price N       USD per 1M cached-input tokens (default: 0.075, placeholder)

HTTPS + JWT validation (production hardening — opt-in):
If any of the flags below are provided, ALL of --custom-domain and
--hosted-zone-id are required for HTTPS. Without them the collector deploys
in HTTP-only mode, which is OK for sandbox but publishes Codex telemetry
over the public internet unauthenticated (trust-on-distribution).

  --custom-domain FQDN         FQDN for the collector ALB (e.g. otel.codex.example.com).
                               ACM cert is provisioned automatically via DNS validation.
  --hosted-zone-id ID          Route 53 hosted zone ID that owns the FQDN.
  --oidc-issuer URL            OIDC issuer URL (e.g. https://cognito-idp.<region>.amazonaws.com/<pool-id>).
  --oidc-jwks URL              JWKS endpoint (typically <issuer>/.well-known/jwks.json).
  --oidc-client-id ID          OIDC app client ID — used as 'aud' claim validation at the ALB.

  -h, --help                   Show this help

Examples:
  # Sandbox deploy in us-west-2
  deploy-otel-stack.sh --region us-west-2

  # Production with HTTPS + Cognito JWT validation
  deploy-otel-stack.sh \
      --region us-west-2 \
      --custom-domain otel.codex.example.com \
      --hosted-zone-id Z1234567890ABC \
      --oidc-issuer https://cognito-idp.us-west-2.amazonaws.com/us-west-2_AbCdEf123 \
      --oidc-jwks   https://cognito-idp.us-west-2.amazonaws.com/us-west-2_AbCdEf123/.well-known/jwks.json \
      --oidc-client-id 1a2b3c4d5e6f7g8h

After deploy completes, the collector endpoint is printed. Paste it into your
Codex config.toml under the [otel] section, e.g.:

  [otel]
  exporter = "otlp-http"
  endpoint = "<collector-endpoint>"

When JWT validation is enabled, each developer also needs to supply a bearer
token. See OpenAI Codex configuration reference:
https://developers.openai.com/codex/config-advanced
EOF
}

region="us-west-2"
aws_profile=""
prefix="codex-otel"
dashboard_name="CodexOnBedrock"
input_price="0.15"
output_price="0.60"
cached_input_price="0.075"
custom_domain=""
hosted_zone_id=""
oidc_issuer=""
oidc_jwks=""
oidc_client_id=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) region="${2:?--region requires a value}"; shift 2;;
    --aws-profile) aws_profile="${2:?--aws-profile requires a value}"; shift 2;;
    --stack-prefix) prefix="${2:?--stack-prefix requires a value}"; shift 2;;
    --dashboard-name) dashboard_name="${2:?--dashboard-name requires a value}"; shift 2;;
    --input-price) input_price="${2:?--input-price requires a value}"; shift 2;;
    --output-price) output_price="${2:?--output-price requires a value}"; shift 2;;
    --cached-input-price) cached_input_price="${2:?--cached-input-price requires a value}"; shift 2;;
    --custom-domain) custom_domain="${2:?--custom-domain requires a value}"; shift 2;;
    --hosted-zone-id) hosted_zone_id="${2:?--hosted-zone-id requires a value}"; shift 2;;
    --oidc-issuer) oidc_issuer="${2:?--oidc-issuer requires a value}"; shift 2;;
    --oidc-jwks) oidc_jwks="${2:?--oidc-jwks requires a value}"; shift 2;;
    --oidc-client-id) oidc_client_id="${2:?--oidc-client-id requires a value}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Error: unknown flag: $1" >&2; echo "Run with --help for usage." >&2; exit 2;;
  esac
done

# ----------------------------------------------------------------------------
# Pre-deployment validation
# ----------------------------------------------------------------------------
err()  { printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*" >&2; }
log()  { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }

# Apply --aws-profile by exporting AWS_PROFILE so all aws CLI calls pick it up.
if [[ -n "$aws_profile" ]]; then
  export AWS_PROFILE="$aws_profile"
fi

if ! command -v aws >/dev/null 2>&1; then
  err "AWS CLI v2 is required but was not found in PATH."
  err "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  exit 1
fi

# Region format: lowercase letters + digits, e.g. us-west-2, eu-central-1
if ! [[ "$region" =~ ^[a-z]{2}-[a-z]+-[0-9]+$ ]]; then
  err "Invalid --region value: '$region' (expected format like 'us-west-2')."
  exit 1
fi

# Numeric price flags
for var_name in input_price output_price cached_input_price; do
  val="${!var_name}"
  if ! [[ "$val" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    err "--${var_name//_/-} must be a non-negative number; got '$val'."
    exit 1
  fi
done

# Stack prefix sanity (CloudFormation stack-name allows [a-zA-Z][-a-zA-Z0-9]*)
if ! [[ "$prefix" =~ ^[a-zA-Z][-a-zA-Z0-9]*$ ]]; then
  err "Invalid --stack-prefix '$prefix' (must match [a-zA-Z][-a-zA-Z0-9]*)."
  exit 1
fi

# Verify credentials work against the chosen region.
if ! aws sts get-caller-identity --region "$region" >/dev/null 2>&1; then
  err "AWS credentials are not configured or do not have access in region '$region'."
  err "Try one of:"
  err "  - export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY"
  err "  - aws sso login --profile <your-profile>  (and pass --aws-profile <your-profile>)"
  err "  - aws configure"
  exit 1
fi

# HTTPS / JWT correlation: ALB jwt-validation action is HTTPS-only.
# Allow either to be set independently, but warn if JWT is requested without HTTPS.
https_on=0; jwt_on=0
[[ -n "$custom_domain" && -n "$hosted_zone_id" ]] && https_on=1
if [[ -n "$custom_domain" && -z "$hosted_zone_id" ]] || [[ -z "$custom_domain" && -n "$hosted_zone_id" ]]; then
  err "--custom-domain and --hosted-zone-id must be set together for HTTPS."
  exit 1
fi
[[ -n "$oidc_issuer" && -n "$oidc_jwks" ]] && jwt_on=1
if [[ -n "$oidc_issuer" && -z "$oidc_jwks" ]] || [[ -z "$oidc_issuer" && -n "$oidc_jwks" ]]; then
  err "--oidc-issuer and --oidc-jwks must be set together."
  exit 1
fi
if (( jwt_on == 1 && https_on == 0 )); then
  warn "--oidc-* flags require HTTPS (--custom-domain + --hosted-zone-id). JWT validation will be skipped."
fi

# Templates must exist
infra_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../infrastructure" && pwd)"
for tpl in networking.yaml otel-collector.yaml codex-otel-dashboard.yaml; do
  if [[ ! -f "$infra_dir/$tpl" ]]; then
    err "CloudFormation template not found: $infra_dir/$tpl"
    exit 1
  fi
done

# ----------------------------------------------------------------------------
# Deploy
# ----------------------------------------------------------------------------
net_stack="${prefix}-networking"
col_stack="${prefix}-collector"
dash_stack="${prefix}-dashboard"

log "Deploying networking stack: $net_stack"
aws cloudformation deploy \
  --region "$region" \
  --stack-name "$net_stack" \
  --template-file "$infra_dir/networking.yaml" \
  --no-fail-on-empty-changeset >/dev/null
ok "networking ready"

vpc_id=$(aws cloudformation describe-stacks --region "$region" --stack-name "$net_stack" \
  --query "Stacks[0].Outputs[?OutputKey=='VpcId'].OutputValue" --output text)
subnet_ids=$(aws cloudformation describe-stacks --region "$region" --stack-name "$net_stack" \
  --query "Stacks[0].Outputs[?OutputKey=='SubnetIds'].OutputValue" --output text)

collector_params=(VpcId="$vpc_id" SubnetIds="$subnet_ids")
[[ -n "$custom_domain" ]]    && collector_params+=(CustomDomainName="$custom_domain")
[[ -n "$hosted_zone_id" ]]   && collector_params+=(HostedZoneId="$hosted_zone_id")
[[ -n "$oidc_issuer" ]]      && collector_params+=(OidcIssuerUrl="$oidc_issuer")
[[ -n "$oidc_jwks" ]]        && collector_params+=(OidcJwksEndpoint="$oidc_jwks")
[[ -n "$oidc_client_id" ]]   && collector_params+=(OidcClientId="$oidc_client_id")

if (( https_on == 1 && jwt_on == 1 )); then
  log "Collector posture: HTTPS + JWT validation (domain=$custom_domain issuer=$oidc_issuer)"
elif (( https_on == 1 )); then
  log "Collector posture: HTTPS, no auth (encrypted in transit; attribution is header-based)"
else
  log "Collector posture: HTTP, no auth (sandbox default — data is NOT encrypted in transit)"
fi

log "Deploying collector stack: $col_stack (VPC $vpc_id)"
aws cloudformation deploy \
  --region "$region" \
  --stack-name "$col_stack" \
  --template-file "$infra_dir/otel-collector.yaml" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "${collector_params[@]}" \
  --no-fail-on-empty-changeset >/dev/null
ok "collector ready"

collector_endpoint=$(aws cloudformation describe-stacks --region "$region" --stack-name "$col_stack" \
  --query "Stacks[0].Outputs[?OutputKey=='CollectorEndpoint'].OutputValue" --output text)

log "Deploying dashboard stack: $dash_stack"
aws cloudformation deploy \
  --region "$region" \
  --stack-name "$dash_stack" \
  --template-file "$infra_dir/codex-otel-dashboard.yaml" \
  --parameter-overrides \
      DashboardName="$dashboard_name" \
      InputTokenPriceUsdPerMillion="$input_price" \
      OutputTokenPriceUsdPerMillion="$output_price" \
      CachedInputTokenPriceUsdPerMillion="$cached_input_price" \
  --no-fail-on-empty-changeset >/dev/null
ok "dashboard ready"

dashboard_url=$(aws cloudformation describe-stacks --region "$region" --stack-name "$dash_stack" \
  --query "Stacks[0].Outputs[?OutputKey=='DashboardURL'].OutputValue" --output text)

cat <<EOF

==========================================================================
Codex OTel stack deployed.

Collector endpoint:  $collector_endpoint
Dashboard:           $dashboard_url

Next step — point Codex at the collector by appending this block to
~/.codex/config.toml:

  [otel]
  exporter = "otlp-http"
  endpoint = "$collector_endpoint"

For the full Codex configuration reference, see:
  https://developers.openai.com/codex/config-advanced

Teardown (reverse order):
  aws cloudformation delete-stack --region $region --stack-name $dash_stack
  aws cloudformation delete-stack --region $region --stack-name $col_stack
  aws cloudformation delete-stack --region $region --stack-name $net_stack
==========================================================================
EOF
