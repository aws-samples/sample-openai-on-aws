# Reference — Region Availability

This repository does not maintain a hard-coded Bedrock region × model matrix.
Availability changes over time, can differ by account, and should be verified
against current AWS documentation and your own AWS account.

OpenAI recommends the latest GPT-5 family model for Codex. In practice, prefer
`openai.gpt-5.5` when your Bedrock region and account support it, and use
`openai.gpt-5.4` when you need a fallback. The custom-provider examples in this
repo keep `wire_api = "responses"` explicit for clarity, although Responses is
already the default for Codex custom providers.

## Source of truth

- AWS Bedrock documentation for OpenAI model availability is the source of truth.
- Account-level verification is the final check: a model may exist in AWS docs
  but still require model access or account enablement in your region.

## Endpoints

- **Mantle (OpenAI-compatible API):** `bedrock-mantle.<region>.api.aws/openai/v1` — serves GPT-5.4, GPT-5.5, and GPT-OSS models. The LiteLLM Gateway uses LiteLLM's `bedrock_mantle/<model>` provider and keeps Codex traffic on the OpenAI-compatible Responses path.

> **Note:** The LiteLLM gateway sample in this repo now resolves the Mantle
> endpoint from the gateway's selected Bedrock region. The tested walkthrough
> uses `us-east-1`, but the same image can target a different region as long as
> the gateway mints the bearer token and calls the Mantle endpoint in that same
> region.

Under the hood, Mantle authenticates with a Bearer token
(`Authorization: Bearer <key>`). The LiteLLM gateway sample in this repo now
refreshes `AWS_BEARER_TOKEN_BEDROCK` automatically from the gateway's AWS
credentials using the official `aws-bedrock-token-generator` package. For
direct manual API testing, you can still generate a short-term key (12h) from
your IAM credentials:
```bash
pip install aws-bedrock-token-generator
python -c "from aws_bedrock_token_generator import provide_token; print(provide_token())"
```

## How to verify availability

1. Check the current AWS Bedrock documentation for the model you want.
2. Verify the model appears in your account for the target region:

```bash
aws bedrock list-foundation-models \
  --region <region> \
  --query "modelSummaries[?contains(modelId,'openai')].modelId" \
  --output text
```

If a model ID you need is not in that list, model access is likely not enabled
for the account in that region. Request access in the **Amazon Bedrock** →
**Model access** console page.

## Quotas

Per-account Bedrock invoke quotas apply. Check the Service Quotas console under
**Amazon Bedrock** and filter by the specific model ID.

For live dashboards of quota consumption, see `operate-monitoring.md` ("Quota
monitoring" section).
