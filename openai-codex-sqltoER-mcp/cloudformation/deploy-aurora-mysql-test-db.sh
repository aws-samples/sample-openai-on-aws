#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEMPLATE_FILE="${SCRIPT_DIR}/aurora-mysql-test-db.yaml"

AWS_PROFILE_NAME="${AWS_PROFILE_NAME:-mcp}"
AWS_REGION_NAME="${AWS_REGION_NAME:-us-west-2}"
STACK_NAME="${STACK_NAME:-sql-to-erdiag-codex}"
DATABASE_NAME="${DATABASE_NAME:-workshop}"
READONLY_USERNAME="${READONLY_USERNAME:-readonly_user}"
DB_INSTANCE_CLASS="${DB_INSTANCE_CLASS:-db.t4g.medium}"
LAYER_NAME="${LAYER_NAME:-pymysql-python312}"
LAYER_BUILD_DIR="${LAYER_BUILD_DIR:-/tmp/pymysql-layer}"
LAYER_ZIP="${LAYER_ZIP:-/tmp/pymysql-layer.zip}"

aws_mcp() {
  env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_SESSION_TOKEN \
    AWS_PROFILE="${AWS_PROFILE_NAME}" \
    AWS_REGION="${AWS_REGION_NAME}" \
    aws "$@"
}

if [ "${1:-}" = "--delete" ]; then
  aws_mcp cloudformation delete-stack \
    --region "${AWS_REGION_NAME}" \
    --stack-name "${STACK_NAME}"
  echo "Delete started for stack ${STACK_NAME} in ${AWS_REGION_NAME}."
  exit 0
fi

desktop_ip="$(curl -fsS https://checkip.amazonaws.com | tr -d '\n')"
desktop_egress_pool_cidr="$(printf '%s\n' "${desktop_ip}" | awk -F. '{print $1 "." $2 "." $3 ".0/24"}')"

vpc_id="$(aws_mcp ec2 describe-vpcs \
  --region "${AWS_REGION_NAME}" \
  --filters Name=is-default,Values=true \
  --query 'Vpcs[0].VpcId' \
  --output text)"

public_subnet_ids="$(aws_mcp ec2 describe-subnets \
  --region "${AWS_REGION_NAME}" \
  --filters Name=vpc-id,Values="${vpc_id}" Name=map-public-ip-on-launch,Values=true \
  --query 'Subnets[].SubnetId' \
  --output text | tr '\t' ',')"

public_route_table_ids="$(aws_mcp ec2 describe-route-tables \
  --region "${AWS_REGION_NAME}" \
  --filters Name=vpc-id,Values="${vpc_id}" \
  --query "RouteTables[?Routes[?GatewayId && starts_with(GatewayId, 'igw-')]].RouteTableId" \
  --output text | tr '\t' ',')"

s3_prefix_list_id="$(aws_mcp ec2 describe-managed-prefix-lists \
  --region "${AWS_REGION_NAME}" \
  --filters Name=prefix-list-name,Values="com.amazonaws.${AWS_REGION_NAME}.s3" \
  --query 'PrefixLists[0].PrefixListId' \
  --output text)"

rm -rf "${LAYER_BUILD_DIR}" "${LAYER_ZIP}"
mkdir -p "${LAYER_BUILD_DIR}/python"
python3 -m pip install \
  -r "${PROJECT_ROOT}/lambda-layers/pymysql/requirements.txt" \
  -t "${LAYER_BUILD_DIR}/python"
(cd "${LAYER_BUILD_DIR}" && zip -qr "${LAYER_ZIP}" python)

pymysql_layer_arn="$(aws_mcp lambda publish-layer-version \
  --region "${AWS_REGION_NAME}" \
  --layer-name "${LAYER_NAME}" \
  --zip-file "fileb://${LAYER_ZIP}" \
  --compatible-runtimes python3.12 \
  --query 'LayerVersionArn' \
  --output text)"

echo "Deploying ${STACK_NAME} in ${AWS_REGION_NAME}"
echo "AWS profile: ${AWS_PROFILE_NAME}"
echo "VPC: ${vpc_id}"
echo "Public subnets: ${public_subnet_ids}"
echo "Public route tables: ${public_route_table_ids}"
echo "Desktop egress pool: ${desktop_egress_pool_cidr}"
echo "PyMySQL layer: ${pymysql_layer_arn}"

aws_mcp cloudformation deploy \
  --region "${AWS_REGION_NAME}" \
  --stack-name "${STACK_NAME}" \
  --template-file "${TEMPLATE_FILE}" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    VpcId="${vpc_id}" \
    PublicSubnetIds="${public_subnet_ids}" \
    PublicRouteTableIds="${public_route_table_ids}" \
    DesktopEgressPoolCidr="${desktop_egress_pool_cidr}" \
    DatabaseName="${DATABASE_NAME}" \
    ReadOnlyUsername="${READONLY_USERNAME}" \
    DbInstanceClass="${DB_INSTANCE_CLASS}" \
    PyMySQLLayerArn="${pymysql_layer_arn}" \
    S3GatewayPrefixListId="${s3_prefix_list_id}" \
    DeletionProtectionEnabled=false

aws_mcp cloudformation describe-stacks \
  --region "${AWS_REGION_NAME}" \
  --stack-name "${STACK_NAME}" \
  --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' \
  --output table
