#!/usr/bin/env bash
# ABOUTME: Interactive deployment script for Cognito User Pool with optional custom domain
# ABOUTME: Supports both interactive and non-interactive modes for flexible deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../infrastructure" && pwd)"

# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------
print_help() {
  cat <<EOF
Deploy Cognito User Pool for Codex with Bedrock

This script provisions an Amazon Cognito User Pool that can act as the OIDC
provider for the Codex LLM Gateway (LiteLLM JWT middleware) or for any other
component requiring OIDC.

Usage:
  Interactive mode (prompts for all values):
    $0

  Non-interactive mode (fully scripted):
    $0 --stack-name <name> --region <region> [options]

Required (in non-interactive mode):
  --stack-name <name>         CloudFormation stack name (CFN: [a-zA-Z][-a-zA-Z0-9]*)
  --region <region>           AWS region (e.g. us-west-2)

Optional:
  --aws-profile <profile>     AWS named profile to use (otherwise uses
                              default credential chain)
  --user-pool-name <name>     Cognito User Pool name (defaults to stack name)
  --domain-prefix <prefix>    Domain prefix for the default Cognito-managed
                              domain. Cannot contain the reserved word
                              'cognito'. Defaults to stack name with
                              'cognito' replaced by 'auth'.
  --custom-domain <domain>    Optional custom domain (e.g. auth.example.com).
                              When set, an ACM cert in us-east-1 is
                              provisioned automatically via DNS validation.
  --hosted-zone-id <id>       Route 53 Hosted Zone ID. Required when
                              --custom-domain is set. Format: Z[A-Z0-9]+.
  -h, --help                  Show this help message

Examples:
  # Interactive mode
  $0

  # Default Cognito-managed domain
  $0 --stack-name my-cognito --region us-east-1

  # Custom domain in us-east-1
  $0 --stack-name my-cognito --region us-east-1 \\
     --custom-domain auth.example.com --hosted-zone-id Z123ABC

  # Custom domain in different region (cert still goes to us-east-1)
  $0 --stack-name my-cognito --region us-west-2 \\
     --custom-domain auth.example.com --hosted-zone-id Z123ABC \\
     --aws-profile my-admin-profile
EOF
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
STACK_NAME=""
REGION=""
AWS_PROFILE_ARG=""
CUSTOM_DOMAIN=""
HOSTED_ZONE_ID=""
USER_POOL_NAME=""
DOMAIN_PREFIX=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --stack-name)        STACK_NAME="${2:?--stack-name requires a value}"; shift 2;;
    --region)            REGION="${2:?--region requires a value}"; shift 2;;
    --aws-profile)       AWS_PROFILE_ARG="${2:?--aws-profile requires a value}"; shift 2;;
    --custom-domain)     CUSTOM_DOMAIN="${2:?--custom-domain requires a value}"; shift 2;;
    --hosted-zone-id)    HOSTED_ZONE_ID="${2:?--hosted-zone-id requires a value}"; shift 2;;
    --user-pool-name)    USER_POOL_NAME="${2:?--user-pool-name requires a value}"; shift 2;;
    --domain-prefix)     DOMAIN_PREFIX="${2:?--domain-prefix requires a value}"; shift 2;;
    -h|--help)           print_help; exit 0;;
    *)
      echo "Error: Unknown option: $1" >&2
      echo "Run with --help for usage information." >&2
      exit 2
      ;;
  esac
done

# Apply --aws-profile by exporting AWS_PROFILE so all aws CLI calls pick it up.
if [[ -n "$AWS_PROFILE_ARG" ]]; then
  export AWS_PROFILE="$AWS_PROFILE_ARG"
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
err() { echo "Error: $*" >&2; }

prompt_input() {
  local prompt="$1"
  local default="$2"
  local result

  if [ -n "$default" ]; then
    read -p "$prompt [$default]: " result
    echo "${result:-$default}"
  else
    read -p "$prompt: " result
    echo "$result"
  fi
}

prompt_yn() {
  local prompt="$1"
  local default="$2"
  local result

  if [ "$default" = "y" ]; then
    read -p "$prompt [Y/n]: " result
    result="${result:-y}"
  else
    read -p "$prompt [y/N]: " result
    result="${result:-n}"
  fi

  [[ "$result" =~ ^[Yy] ]]
}

# ---------------------------------------------------------------------------
# Pre-flight checks (run regardless of interactive vs non-interactive)
# ---------------------------------------------------------------------------
if ! command -v aws >/dev/null 2>&1; then
  err "AWS CLI v2 is required but was not found in PATH."
  err "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  exit 1
fi

# Templates must exist
for tpl in cognito-user-pool-setup.yaml cognito-custom-domain-cert.yaml; do
  if [[ ! -f "$INFRA_DIR/$tpl" ]]; then
    err "CloudFormation template not found: $INFRA_DIR/$tpl"
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# Interactive mode (only when no required flags provided)
# ---------------------------------------------------------------------------
if [ -z "$STACK_NAME" ] && [ -z "$REGION" ]; then
  echo "╭────────────────────────────────────────────────────────────╮"
  echo "│  Cognito User Pool Deployment for Codex with Bedrock       │"
  echo "╰────────────────────────────────────────────────────────────╯"
  echo ""

  # Get current AWS account and region
  CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
  CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

  echo "Current AWS Account: $CURRENT_ACCOUNT"
  echo ""

  STACK_NAME=$(prompt_input "Stack name" "codex-cognito")
  REGION=$(prompt_input "AWS Region" "$CURRENT_REGION")
  USER_POOL_NAME=$(prompt_input "User Pool name" "$STACK_NAME")

  echo ""
  if prompt_yn "Use custom domain?" "n"; then
    CUSTOM_DOMAIN=$(prompt_input "Custom domain (e.g., auth.example.com)" "")

    if [ -n "$CUSTOM_DOMAIN" ]; then
      DOMAIN_PARTS=(${CUSTOM_DOMAIN//./ })
      if [ ${#DOMAIN_PARTS[@]} -ge 2 ]; then
        PARTS_COUNT=${#DOMAIN_PARTS[@]}
        SECOND_LAST_IDX=$((PARTS_COUNT - 2))
        LAST_IDX=$((PARTS_COUNT - 1))
        ROOT_DOMAIN="${DOMAIN_PARTS[$SECOND_LAST_IDX]}.${DOMAIN_PARTS[$LAST_IDX]}"

        echo ""
        echo "Looking for Route 53 hosted zone for $ROOT_DOMAIN..."
        FOUND_ZONE=$(aws route53 list-hosted-zones \
          --query "HostedZones[?Name=='${ROOT_DOMAIN}.'].Id" \
          --output text 2>/dev/null | sed 's/\/hostedzone\///')

        if [ -n "$FOUND_ZONE" ]; then
          echo "Found hosted zone: $FOUND_ZONE"
          HOSTED_ZONE_ID=$(prompt_input "Route 53 Hosted Zone ID" "$FOUND_ZONE")
        else
          echo "No hosted zone found for $ROOT_DOMAIN"
          HOSTED_ZONE_ID=$(prompt_input "Route 53 Hosted Zone ID" "")
        fi
      else
        HOSTED_ZONE_ID=$(prompt_input "Route 53 Hosted Zone ID" "")
      fi
    fi
  else
    DOMAIN_PREFIX=$(prompt_input "Domain prefix for Cognito domain" "$STACK_NAME")
  fi

  # Confirm
  echo ""
  echo "╭─── Configuration Summary ───╮"
  echo "│ Stack Name:    $STACK_NAME"
  echo "│ Region:        $REGION"
  echo "│ User Pool:     $USER_POOL_NAME"
  if [ -n "$CUSTOM_DOMAIN" ]; then
    echo "│ Custom Domain: $CUSTOM_DOMAIN"
    echo "│ Hosted Zone:   $HOSTED_ZONE_ID"
  else
    echo "│ Domain Prefix: $DOMAIN_PREFIX"
    echo "│ Full Domain:   ${DOMAIN_PREFIX}.auth.${REGION}.amazoncognito.com"
  fi
  echo "╰─────────────────────────────╯"
  echo ""

  if ! prompt_yn "Proceed with deployment?" "y"; then
    echo "Deployment cancelled"
    exit 0
  fi

  echo ""
fi

# ---------------------------------------------------------------------------
# Validate required parameters (post-interactive, post-CLI)
# ---------------------------------------------------------------------------
if [ -z "$STACK_NAME" ] || [ -z "$REGION" ]; then
  err "Missing required parameters: --stack-name and --region are both required."
  err "Run with --help for usage information."
  exit 1
fi

# CloudFormation stack-name format
if ! [[ "$STACK_NAME" =~ ^[a-zA-Z][-a-zA-Z0-9]*$ ]]; then
  err "Invalid --stack-name '$STACK_NAME' (must match [a-zA-Z][-a-zA-Z0-9]*)."
  exit 1
fi

# Region format
if ! [[ "$REGION" =~ ^[a-z]{2}-[a-z]+-[0-9]+$ ]]; then
  err "Invalid --region value: '$REGION' (expected format like 'us-west-2')."
  exit 1
fi

# Verify credentials work
if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
  err "AWS credentials are not configured or do not have access in region '$REGION'."
  err "Try one of:"
  err "  - export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY"
  err "  - aws sso login --profile <your-profile> (and pass --aws-profile <your-profile>)"
  err "  - aws configure"
  exit 1
fi

# Default values
USER_POOL_NAME=${USER_POOL_NAME:-$STACK_NAME}

# Default domain prefix - avoid reserved word "cognito"
if [ -z "$DOMAIN_PREFIX" ]; then
  DOMAIN_PREFIX=$(echo "$STACK_NAME" | sed 's/cognito/auth/gi')
fi

# Validate domain prefix doesn't contain "cognito" (reserved word)
if [ -n "$DOMAIN_PREFIX" ] && echo "$DOMAIN_PREFIX" | grep -qi "cognito"; then
  err "Domain prefix cannot contain the reserved word 'cognito'."
  err "  Current value: $DOMAIN_PREFIX"
  err "  Pass --domain-prefix with a different value."
  exit 1
fi

# Custom-domain coupling
if [ -n "$CUSTOM_DOMAIN" ]; then
  if [ -z "$HOSTED_ZONE_ID" ]; then
    err "--hosted-zone-id is required when using --custom-domain."
    exit 1
  fi
  if ! [[ "$HOSTED_ZONE_ID" =~ ^Z[A-Z0-9]+$ ]]; then
    err "Invalid --hosted-zone-id '$HOSTED_ZONE_ID' (expected format like 'Z1234567890ABC')."
    exit 1
  fi
fi
if [ -z "$CUSTOM_DOMAIN" ] && [ -n "$HOSTED_ZONE_ID" ]; then
  err "--hosted-zone-id was supplied without --custom-domain. Either pass both or neither."
  exit 1
fi

# ---------------------------------------------------------------------------
# Deploy
# ---------------------------------------------------------------------------
if [ -n "$CUSTOM_DOMAIN" ]; then
  USE_CUSTOM_DOMAIN="true"

  # Always use two-stack approach for custom domains
  # Certificate stack is always in us-east-1 (Cognito requirement)
  echo "→ Custom domain requires certificate in us-east-1"
  echo "→ Using two-stack deployment approach..."

  # Extract parent domain from custom domain (e.g., "example.com" from "auth.example.com")
  DOMAIN_PARTS=(${CUSTOM_DOMAIN//./ })
  PARTS_COUNT=${#DOMAIN_PARTS[@]}
  SECOND_LAST_IDX=$((PARTS_COUNT - 2))
  LAST_IDX=$((PARTS_COUNT - 1))
  PARENT_DOMAIN="${DOMAIN_PARTS[$SECOND_LAST_IDX]}.${DOMAIN_PARTS[$LAST_IDX]}"

  echo "→ Checking parent domain: $PARENT_DOMAIN"

  # Check if parent domain has an A record
  PARENT_A_RECORD=$(aws route53 list-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --query "ResourceRecordSets[?Name=='${PARENT_DOMAIN}.' && Type=='A']" \
    --output json)

  if [ "$PARENT_A_RECORD" = "[]" ]; then
    echo "⚠ Parent domain has no A record - will create placeholder"
    CREATE_PARENT_RECORD="true"
  else
    echo "✓ Parent domain has A record"
    CREATE_PARENT_RECORD="false"
  fi

  CERT_STACK_NAME="${STACK_NAME}-cert"

  # Deploy or update certificate stack
  if aws cloudformation describe-stacks --region us-east-1 --stack-name "$CERT_STACK_NAME" &>/dev/null; then
    echo "→ Updating certificate stack in us-east-1..."
  else
    echo "→ Creating certificate stack in us-east-1..."
  fi

  aws cloudformation deploy \
    --region us-east-1 \
    --template-file "$INFRA_DIR/cognito-custom-domain-cert.yaml" \
    --stack-name "$CERT_STACK_NAME" \
    --parameter-overrides \
      CustomDomainName="$CUSTOM_DOMAIN" \
      Route53HostedZoneId="$HOSTED_ZONE_ID" \
      ParentDomainName="$PARENT_DOMAIN" \
      CreateParentDomainRecord="$CREATE_PARENT_RECORD" \
    --no-fail-on-empty-changeset

  if [ $? -ne 0 ]; then
    err "Failed to deploy certificate stack"
    exit 1
  fi

  echo "✓ Certificate stack deployed successfully"

  CERT_ARN=$(aws cloudformation describe-stacks \
    --region us-east-1 \
    --stack-name "$CERT_STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CertificateArn`].OutputValue' \
    --output text)

  if [ -z "$CERT_ARN" ]; then
    err "Failed to get certificate ARN from stack outputs"
    exit 1
  fi

  CERT_STATUS=$(aws acm describe-certificate \
    --certificate-arn "$CERT_ARN" \
    --region us-east-1 \
    --query 'Certificate.Status' \
    --output text)

  echo "→ Certificate status: $CERT_STATUS"

  if [ "$CERT_STATUS" != "ISSUED" ]; then
    echo "⚠ Warning: Certificate is not yet issued. Cognito deployment may fail."
    echo "⚠ Wait for DNS validation to complete, then re-run this script."
  fi

  echo "→ Using certificate: $CERT_ARN"

  CERT_PARAM="CertificateArn=$CERT_ARN"
else
  USE_CUSTOM_DOMAIN="false"
  CERT_PARAM=""
fi

# Deploy Cognito stack
echo ""
echo "→ Deploying Cognito User Pool stack..."

PARAMS="UserPoolName=$USER_POOL_NAME DomainPrefix=$DOMAIN_PREFIX UseCustomDomain=$USE_CUSTOM_DOMAIN"

if [ "$USE_CUSTOM_DOMAIN" = "true" ]; then
  PARAMS="$PARAMS CustomDomainName=$CUSTOM_DOMAIN $CERT_PARAM Route53HostedZoneId=$HOSTED_ZONE_ID"
fi

aws cloudformation deploy \
  --region "$REGION" \
  --template-file "$INFRA_DIR/cognito-user-pool-setup.yaml" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides $PARAMS \
  --capabilities CAPABILITY_IAM

echo ""
echo "✓ Cognito User Pool deployed successfully"
echo ""

# Display outputs
echo "╭─── Cognito Stack Outputs ───╮"
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs' \
  --output table

if [ "$USE_CUSTOM_DOMAIN" = "true" ]; then
  echo ""
  echo "╭─── Custom Domain Configured ───╮"
  sleep 2
  echo "✓ Route 53 A record created automatically"
  echo "✓ DNS: $CUSTOM_DOMAIN → CloudFront"
  echo ""
  echo "Note: DNS propagation may take a few minutes"
  echo ""
fi

cat <<EOF

Next steps:
  1. Capture the User Pool ID, Client ID, and Issuer URL from the outputs above.
  2. Build and push the LiteLLM Gateway images, then deploy the gateway stack
     directly with CloudFormation:

        aws cloudformation deploy \\
          --stack-name codex-litellm-gateway \\
          --template-file deployment/litellm/ecs/litellm-ecs.yaml \\
          --capabilities CAPABILITY_NAMED_IAM \\
          --region $REGION \\
          --parameter-overrides \\
              EnableJwtMiddleware=true \\
              JwksUrl=<issuer-url>/.well-known/jwks.json \\
              JwtIssuer=<issuer-url> \\
              JwtAudience=<app-client-id> \\
              ...

     See docs/QUICKSTART_LLM_GATEWAY.md for the full step-by-step guide.

EOF
