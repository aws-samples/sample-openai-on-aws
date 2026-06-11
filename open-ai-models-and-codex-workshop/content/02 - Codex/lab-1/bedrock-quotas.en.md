---
title: "(Optional) Plan capacity by understanding Bedrock service quotas"
weight: 13
---

Amazon Bedrock has service quotas that limit the number of requests and tokens you can use. Understanding these quotas helps you plan team capacity.

:::alert{type="info" header="Why this matters for Codex"}
Codex runs every model call through Bedrock, so a busy team can hit per-account request and token limits. Check these quotas before a team rollout. The exercise is optional for an individual workshop run.
:::

## 1. View current quotas

1. Navigate to the [Service Quotas console for Bedrock](https://console.aws.amazon.com/servicequotas/home/services/bedrock/quotas).

2. Search for "OpenAI" or "GPT" to see quotas for OpenAI models.

![Searching for Bedrock quotas](/static/images/codex/lab-1/pre-bedrock-quotas.png)

:::alert{type="info" header="Quotas may not appear immediately"}
OpenAI model quotas in the Service Quotas console may take some time to appear after model access is granted. If you don't see GPT-5.5 or GPT-5.4 quotas listed for the model your facilitator selected, check back later or contact AWS support.
:::

## 2. Key quotas to monitor

| Quota Name | Default | Description |
|:-----------|:--------|:------------|
| Requests per minute (RPM) | Varies | Maximum API calls per minute |
| Tokens per minute (TPM) | Varies | Maximum input + output tokens per minute |
| Model units per minute | Varies | Compute capacity for inference |

## 3. Request quota increases

If your team needs higher limits:

1. From the Service Quotas console, select the quota you want to increase.
2. Click **Request quota increase**.
3. Enter your desired value and provide a justification.
4. Submit the request.

:::alert{type="info" header="Quota increase timing"}
Quota increases typically take 1-3 business days to process. Plan ahead for team rollouts.
:::

## 4. Calculate team capacity

Estimate your team's needs:

- **Average tokens per request**: ~2,000 input + ~1,000 output = 3,000 tokens
- **Requests per developer per hour**: ~20-50 during active coding
- **Team size**: Number of concurrent developers

**Example calculation**:
- 10 developers × 30 requests/hour × 3,000 tokens = 900,000 tokens/hour
- Required TPM = 900,000 ÷ 60 = 15,000 TPM

## 5. Congratulations!

You understand Bedrock service quotas and how to plan capacity for your team.
