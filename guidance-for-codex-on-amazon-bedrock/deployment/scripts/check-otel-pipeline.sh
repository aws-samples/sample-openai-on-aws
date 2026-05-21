#!/bin/bash
set -e

REGION="${1:-us-west-2}"

echo "========================================="
echo "OTEL Pipeline Diagnostics"
echo "Region: ${REGION}"
echo "========================================="
echo ""

echo "STEP 1: Check if metrics exist in CloudWatch"
echo "---------------------------------------------"
aws cloudwatch list-metrics --namespace LiteLLMGateway --region "${REGION}" --output json | jq -r '.Metrics[] | "\(.MetricName) - Dimensions: \(.Dimensions | length)"' | head -10
echo ""

echo "STEP 2: Check latest metric datapoints (last 2 hours)"
echo "-------------------------------------------------------"
START_TIME=$(date -u -v-2H +%Y-%m-%dT%H:%M:%S)
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
aws cloudwatch get-metric-statistics \
  --namespace LiteLLMGateway \
  --metric-name gen_ai.client.operation.duration \
  --start-time "${START_TIME}" \
  --end-time "${END_TIME}" \
  --period 300 \
  --statistics Average,SampleCount \
  --region "${REGION}" \
  --output json | jq '{DatapointCount: (.Datapoints | length), LatestDatapoints: (.Datapoints | sort_by(.Timestamp) | reverse | .[0:3])}'
echo ""

echo "STEP 3: Check LiteLLM container logs for OTEL export"
echo "------------------------------------------------------"
echo "Looking for 'otel', 'export', '404', 'metrics' in last 30 minutes..."
aws logs tail /ecs/codex-litellm-gateway --region "${REGION}" --since 30m --format short 2>&1 | grep -i "otel\|export\|metrics\|404" | tail -10
echo ""

echo "STEP 4: Check OTEL collector logs for received metrics"
echo "--------------------------------------------------------"
echo "Looking for 'gen_ai', 'litellm', 'metrics' in last 30 minutes..."
aws logs tail /ecs/codex-otel-collector-cluster --region "${REGION}" --since 30m --format short 2>&1 | grep -i "gen_ai\|litellm\|metric" | tail -10
echo ""

echo "STEP 5: Check ECS task status"
echo "-------------------------------"
echo "LiteLLM tasks:"
aws ecs list-tasks --cluster codex-litellm-gateway-cluster --region "${REGION}" --output json | jq -r '.taskArns[]' | wc -l | xargs echo "  Running tasks:"
echo ""
echo "OTEL collector tasks:"
aws ecs list-tasks --cluster codex-otel-collector-cluster --region "${REGION}" --output json | jq -r '.taskArns[]' | wc -l | xargs echo "  Running tasks:"
echo ""

echo "========================================="
echo "Diagnostics complete"
echo "========================================="
