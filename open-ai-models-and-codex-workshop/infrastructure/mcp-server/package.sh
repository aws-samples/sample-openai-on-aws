#!/bin/bash
# Packages the MCP server Lambda for deployment.
# Run this from the infrastructure/mcp-server/ directory.
#
# Usage:
#   ./package.sh [S3_BUCKET] [S3_KEY]
#
# This script:
#   1. Generates workshop.db using seed_database.py
#   2. Zips lambda_function.py + workshop.db
#   3. Optionally uploads to S3 if bucket is provided

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

S3_BUCKET="${1:-}"
S3_KEY="${2:-mcp-server.zip}"

echo "Generating workshop.db..."
python3 seed_database.py

echo "Packaging Lambda zip..."
zip -j mcp-server.zip lambda_function.py workshop.db

echo "Created mcp-server.zip ($(du -h mcp-server.zip | cut -f1))"

if [ -n "$S3_BUCKET" ]; then
    echo "Uploading to s3://${S3_BUCKET}/${S3_KEY}..."
    aws s3 cp mcp-server.zip "s3://${S3_BUCKET}/${S3_KEY}"
    echo "Done. Deploy with:"
    echo "  aws cloudformation deploy \\"
    echo "    --template-file template.yaml \\"
    echo "    --stack-name workshop-mcp-server \\"
    echo "    --parameter-overrides S3Bucket=${S3_BUCKET} S3Key=${S3_KEY} \\"
    echo "    --capabilities CAPABILITY_NAMED_IAM"
else
    echo ""
    echo "To deploy, upload the zip to S3 and run:"
    echo "  ./package.sh <your-s3-bucket>"
fi
