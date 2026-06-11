---
title: "(Optional) Monitor basic costs"
weight: 14
---

Set up AWS Budgets to track and alert on Bedrock spending for your team.

:::alert{type="info" header="Why this matters for Codex"}
Codex usage shows up as Amazon Bedrock spend. Set up budgets and alerts before a team rollout so costs stay visible. The exercise is optional for an individual workshop run.
:::

## 1. Create a Bedrock budget

1. Navigate to the [AWS Budgets console](https://console.aws.amazon.com/billing/home#/budgets).

2. Click **Create budget**.

3. Select **Cost budget** and click **Next**.

4. Configure the budget:
   - **Budget name**: `codex-bedrock-monthly`
   - **Period**: Monthly
   - **Budget amount**: Enter your monthly limit (e.g., $500)

5. Add a filter for Amazon Bedrock:
   - Click **Add filter**
   - Select **Service** → **Amazon Bedrock**

6. Configure alerts:
   - **Alert threshold**: 80%
   - **Email recipients**: Your team's email distribution list

7. Click **Create budget**.

## 2. View Bedrock costs

Monitor current spending in the Cost Explorer:

![Cost Explorer](/static/images/codex/lab-1/iam-idc-cost-explorer.png)

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws ce get-cost-and-usage \
  --time-period Start=$(date -v-7d +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Bedrock"]}}'
:::

## 3. Cost optimization tips

- **Use lower reasoning effort for simple tasks**: Set :code[model_reasoning_effort = "low"]{showCopyAction=false} for routine work
- **Create profiles**: Set up a :code[fast]{showCopyAction=false} profile with low reasoning effort
- **Monitor token usage**: Use :code[/status]{showCopyAction=true} to see session token counts
- **Use prompt caching where supported**: Reusing stable context can reduce cost and latency for repeated prompts

## 4. Congratulations!

You've set up cost monitoring for your Codex deployment on Bedrock.
