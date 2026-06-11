---
title: "(Optional) Monitor per-user usage and cost controls"
weight: 46
---

Quota monitoring tracks user token consumption and sends automated alerts when usage thresholds are exceeded, helping administrators manage costs and prevent unexpected overages.

## 1. Overview

The quota monitoring system is an optional feature that tracks per-user token consumption and sends automated alerts when configurable thresholds are exceeded.

### Key features

- **Per-user token tracking** - Monthly and daily consumption monitoring for each user
- **Configurable limits** - Set limits at user, group, or default levels
- **Automated alerting** - SNS notifications at 80%, 90%, and 100% of limits
- **Cost management** - Helps prevent unexpected overages and bill shock

## 2. Setting up quota tracking

1. Create a DynamoDB table for quota tracking:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb create-table \
  --table-name CodexUserQuotas \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=month,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=month,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
:::

2. Create an SNS topic for alerts:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws sns create-topic --name codex-quota-alerts
:::

3. Subscribe to email notifications:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-2:ACCOUNT_ID:codex-quota-alerts \
  --protocol email \
  --notification-endpoint admin@company.com
:::

## 3. Configuration parameters

Default settings:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Monthly token limit | 225M tokens | Default maximum per user per month |
| Daily token limit | ~8.25M tokens | Daily limit (auto-calculated with burst buffer) |
| Burst buffer percent | 10% | Daily buffer for usage variation (5-25%) |
| Warning threshold | 80% | First alert level |
| Critical threshold | 90% | Second alert level |

## 4. Managing quota policies

### Set user-specific quota

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb put-item \
  --table-name CodexQuotaPolicies \
  --item '{
    "policy_type": {"S": "user"},
    "identifier": {"S": "john.doe@example.com"},
    "monthly_limit": {"N": "500000000"},
    "daily_limit": {"N": "20000000"}
  }'
:::

### Set group quota

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb put-item \
  --table-name CodexQuotaPolicies \
  --item '{
    "policy_type": {"S": "group"},
    "identifier": {"S": "engineering"},
    "monthly_limit": {"N": "400000000"}
  }'
:::

### Set default quota

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb put-item \
  --table-name CodexQuotaPolicies \
  --item '{
    "policy_type": {"S": "default"},
    "identifier": {"S": "default"},
    "monthly_limit": {"N": "225000000"},
    "daily_limit": {"N": "8000000"}
  }'
:::

## 5. CloudWatch alarms

You can also create CloudWatch alarms for usage thresholds:

<!-- TODO: Update screenshot with Codex-specific alarm names (Codex-HighCostUsage, Codex-HighTokenUsage) -->
![CloudWatch Alarms](/static/images/codex/lab-4/cloudwatch-alarms.png)

## 6. Alert types

The system sends two categories of alerts:

- **Monthly token alerts** - Sent when monthly usage exceeds 80%, 90%, or 100% of monthly limit
- **Daily token alerts** - Sent when daily usage exceeds 80%, 90%, or 100% of daily limit

**Sample alert:**

```
Subject: Codex CRITICAL - Monthly Token Quota - 92%

Codex Usage Alert - Monthly Token Quota

User: john.doe@company.com
Alert Level: CRITICAL
Month: November 2025

Current Usage: 207,000,000 tokens
Monthly Limit: 225,000,000 tokens
Percentage Used: 92.0%

Days Remaining in Month: 8
Daily Average: 9,409,091 tokens
Projected Monthly Total: 282,272,727 tokens

---
This alert is sent once per threshold level per month.
```

## 7. Monitoring quota usage

To view current quota usage:

1. Check user quotas in DynamoDB:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb scan \
  --table-name CodexUserQuotas \
  --projection-expression "user_id, total_tokens, daily_tokens"
:::

2. Query specific user usage:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb query \
  --table-name CodexUserQuotas \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid": {"S": "john.doe@example.com"}}'
:::

## 8. Next steps

With quota monitoring deployed, you can:
- Monitor user consumption patterns across individuals and groups
- Prevent unexpected cost overages with automated alerts
- Set up automated responses to quota violations
- Generate usage reports for billing and chargebacks
