# Reference — Regions & Models

Single source of truth for "where can I run Codex on Bedrock, and with which
model IDs." Cross-check against the authoritative AWS GPT-5.4-on-Bedrock
getting-started guide — if that guide disagrees, it takes precedence.

## Partitions

| Partition | Supported | Notes |
|---|---|---|
| `aws` (commercial) | Yes | US commercial regions only. See matrix below. |
| `aws-us-gov` (GovCloud) | Not yet | No OpenAI models published in GovCloud Bedrock at time of writing. Open question for FedRAMP customers (see PLAN). |
| `aws-cn` (China) | Not yet | Not on the OpenAI-on-Bedrock roadmap at time of writing. |

## Region × model matrix

AWS's getting-started guide names `us-west-2` as the GPT-5.4 "Production
region". Run `aws bedrock list-foundation-models --region <region>` to check
availability in any other region as access becomes available.

| Model ID | Endpoint | Notes |
|---|---|---|
| `openai.gpt-5.4` | Mantle | Primary model. Served via `bedrock-mantle.<region>.api.aws/openai/v1/responses`. Codex `amazon-bedrock` provider targets this endpoint. |
| `openai.gpt-oss-120b-1:0` | Standard Converse | Useful for connectivity tests. |
| `openai.gpt-oss-20b-1:0` | Standard Converse | |
| `openai.gpt-oss-safeguard-120b` | Standard Converse | Safeguard variant. |
| `openai.gpt-oss-safeguard-20b` | Standard Converse | Safeguard variant. |

CLI examples in this repository use `us-west-2` as a placeholder. Substitute any region where your target model is activated.

## Endpoints

- **Standard Bedrock (Converse / InvokeModel):** `bedrock-runtime.<region>.amazonaws.com` — serves the `gpt-oss*` family today.
- **Mantle (OpenAI-compatible Responses API):** `bedrock-mantle.<region>.api.aws/openai/v1` — serves GPT-5.4. This is the endpoint the Codex `amazon-bedrock` provider and the LiteLLM Gateway `openai` → Bedrock route target.

Both endpoints accept SigV4 with service name `bedrock` (standard) or service
name `bedrock-mantle` (mantle, e.g. `--aws-sigv4 "aws:amz:us-west-2:bedrock-mantle"`).

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
