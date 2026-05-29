#!/bin/bash
set -e

# Deploy LiteLLM CloudWatch Dashboard
# Usage: ./deploy-litellm-dashboard.sh [region] [dashboard-name]

REGION="${1:-us-west-2}"
DASHBOARD_NAME="${2:-LiteLLMGateway}"
STACK_NAME="codex-litellm-gateway-dashboard"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/../infrastructure/litellm-dashboard.yaml"

echo "Deploying LiteLLM dashboard to region: ${REGION}"
echo "Dashboard name: ${DASHBOARD_NAME}"
echo "Stack name: ${STACK_NAME}"
echo ""

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name "${STACK_NAME}" \
  --template-file "${TEMPLATE}" \
  --parameter-overrides \
      DashboardName="${DASHBOARD_NAME}" \
      MetricsNamespace=LiteLLMGateway \
  --no-fail-on-empty-changeset

echo ""
echo "✅ Dashboard deployed: ${DASHBOARD_NAME}"
echo "   View at: https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${DASHBOARD_NAME}"
