# Reference — Regions & Models

Single source of truth for "where can I run Codex on Bedrock, and with which
model IDs." Cross-check against the authoritative AWS GPT-5.4/GPT-5.5-on-Bedrock
getting-started guide — if that guide disagrees, it takes precedence.

## Partitions

| Partition | Supported | Notes |
|---|---|---|
| `aws` (commercial) | Yes | US commercial regions only. See matrix below. |
| `aws-us-gov` (GovCloud) | Not yet | No OpenAI models published in GovCloud Bedrock at time of writing. Open question for FedRAMP customers (see PLAN). |
| `aws-cn` (China) | Not yet | Not on the OpenAI-on-Bedrock roadmap at time of writing. |

## Region × model matrix

Run `aws bedrock list-foundation-models --region <region>` to check availability
in any region as access expands.

| Model ID | Endpoint | Regions | API | Notes |
|---|---|---|---|---|
| `openai.gpt-5.5` | Mantle | `us-east-2` | Responses only | Compatible with Codex via LiteLLM `route_all_chat_openai_to_responses`. |
| `openai.gpt-5.4` | Mantle | `us-east-2`, `us-west-2`, `us-gov-west-1` | Responses only | **Recommended default.** Compatible with Codex via LiteLLM `route_all_chat_openai_to_responses`. |
| `openai.gpt-oss-safeguard-120b` | Mantle | `us-east-2`, `us-west-2`, `us-east-1` | Chat Completions | Maps to `gpt-4o` alias in gateway. |
| `openai.gpt-oss-safeguard-20b` | Mantle | `us-east-2`, `us-west-2`, `us-east-1` | Chat Completions | Maps to `gpt-4o-mini` alias in gateway. |
| `openai.gpt-oss-120b` | Mantle | `us-east-2`, `us-west-2`, `us-east-1` | Chat Completions + Responses | Full API support. |
| `openai.gpt-oss-20b` | Mantle | `us-east-2`, `us-west-2`, `us-east-1` | Chat Completions + Responses | Full API support. |

The LiteLLM gateway config uses `us-east-2` for both models (single Bedrock API key scope). For GPT-5.4 in `us-west-2` or `us-gov-west-1`, update `api_base` in `litellm_config.yaml` and regenerate the key with `AWS_DEFAULT_REGION=<region>`.

## Endpoints

- **Mantle (OpenAI-compatible API):** `bedrock-mantle.<region>.api.aws/openai/v1` — serves GPT-5.4, GPT-5.5, and GPT-OSS models. Used by the LiteLLM Gateway via the `openai/` provider prefix with `route_all_chat_openai_to_responses: true` for GPT-5.x.

> **Note:** The LiteLLM gateway config uses `us-east-2` for both GPT-5.4 and GPT-5.5 because the Bedrock API key must be scoped to a single region. GPT-5.4 is also available in `us-west-2` and `us-gov-west-1` — override the `api_base` and set `AWS_DEFAULT_REGION=<region>` when generating the key if you need a different region.

Authenticates with a Bedrock API key as a Bearer token (`Authorization: Bearer <key>`). Generate a short-term key (12h) from your IAM credentials:
```bash
pip install aws-bedrock-token-generator
python -c "from aws_bedrock_token_generator import provide_token; print(provide_token())"
```

## Quotas

Per-account Bedrock invoke quotas apply. Check the Service Quotas console under
**Amazon Bedrock** and filter by the specific model ID. The AWS guide does not
publish a public default quota number; confirm with your AWS account team for
GPT-5.4 before a production rollout.

For live dashboards of quota consumption, see `operate-monitoring.md` ("Quota
monitoring" section).

## Verifying availability yourself

```bash
aws bedrock list-foundation-models \
  --region us-west-2 \
  --query "modelSummaries[?contains(modelId,'openai')].modelId" \
  --output text
```

If a model ID you need is not in that list, model access is likely not enabled
for the account in that region. Request access in the **Amazon Bedrock** →
**Model access** console page.
