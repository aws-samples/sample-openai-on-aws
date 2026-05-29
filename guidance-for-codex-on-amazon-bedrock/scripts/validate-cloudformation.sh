#!/bin/bash
# ABOUTME: Validates CloudFormation templates using AWS CLI
# ABOUTME: Used by pre-commit hooks to ensure templates are valid before committing

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI not found. Skipping AWS validation.${NC}"
    echo "   Install AWS CLI for complete CloudFormation validation."
    exit 0
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS credentials not configured. Skipping AWS validation.${NC}"
    echo "   Configure AWS credentials for complete CloudFormation validation."
    exit 0
fi

# Validate each template passed as argument
for template in "$@"; do
    # Only validate files in deployment/infrastructure directory
    if [[ "$template" == *"deployment/infrastructure"* ]]; then
        echo -n "Validating $template with AWS CLI... "
        
        # Create a temporary file for error output
        ERROR_FILE=$(mktemp)
        
        # Use AWS CLI to validate template
        if aws cloudformation validate-template \
            --template-body file://"$template" \
            --region us-east-1 >/dev/null 2>"$ERROR_FILE"; then
            echo -e "${GREEN}✅${NC}"
        else
            echo -e "${RED}❌${NC}"
            echo -e "${RED}CloudFormation validation failed for $template:${NC}"
            cat "$ERROR_FILE"
            rm -f "$ERROR_FILE"
            exit 1
        fi
        
        rm -f "$ERROR_FILE"
    fi
done

echo -e "${GREEN}All CloudFormation templates are valid!${NC}"