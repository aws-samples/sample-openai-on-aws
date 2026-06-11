---
title: "Setting up metrics collection"
weight: 43
---

This section shows you how to set up metrics collection backends to receive and store Codex telemetry data.

## 1. Available metrics

Codex exports comprehensive usage metrics:

| Metric Name | Description | Unit |
|-------------|-------------|------|
| :code[codex.session.count]{showCopyAction=true} | Count of CLI sessions started | count |
| :code[codex.token.usage]{showCopyAction=true} | Number of tokens used | tokens |
| :code[codex.cost.usage]{showCopyAction=true} | Cost of the Codex session | USD |
| :code[codex.lines_of_code.count]{showCopyAction=true} | Count of lines of code modified | count |
| :code[codex.commit.count]{showCopyAction=true} | Number of git commits created | count |
| :code[codex.pull_request.count]{showCopyAction=true} | Number of pull requests created | count |
| :code[codex.active_time.total]{showCopyAction=true} | Total active time (not idle time) | seconds |

## 2. Setting up CloudWatch integration

For AWS environments, you can send Codex metrics directly to CloudWatch using the AWS Distro for OpenTelemetry (ADOT) collector.

1. Create a CloudWatch log group for Codex metrics:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws logs create-log-group --log-group-name /aws/codex/metrics
:::

2. Create a CloudWatch namespace for metrics:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch put-metric-data \
  --namespace "Codex" \
  --metric-name "test.metric" \
  --value 1 \
  --unit Count
:::

3. Verify the namespace was created:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch list-metrics --namespace Codex
:::

## 3. CloudWatch Insights queries

### Track token usage by user

To track token usage by user:

1. Navigate to [CloudWatch Logs Insights](https://console.aws.amazon.com/cloudwatch/home#logsV2:logs-insights) in the AWS Console.

2. Select the :code[/aws/codex/metrics]{showCopyAction=true} log group.

3. Run this query:

:::code{showCopyAction="true" language="sql" copyAutoReturn="true"}
fields @timestamp, user.id, codex.token.usage
| stats sum(codex.token.usage) by user.id
| sort by sum desc
:::

### Monitor cost trends by department

To monitor cost trends by department:

1. In CloudWatch Logs Insights, select the :code[/aws/codex/metrics]{showCopyAction=true} log group.

2. Run this query:

:::code{showCopyAction="true" language="sql" copyAutoReturn="true"}
fields @timestamp, department, codex.cost.usage
| filter @message like /codex.cost.usage/
| stats sum(codex.cost.usage) as total_cost by department
| sort by total_cost desc
:::

## 4. Setting up alerts

To configure CloudWatch alarms for important thresholds:

1. Create a high cost usage alarm:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch put-metric-alarm \
  --alarm-name "Codex-HighCostUsage" \
  --alarm-description "Alert when daily costs exceed budget" \
  --metric-name "codex.cost.usage" \
  --namespace "Codex" \
  --statistic Sum \
  --period 86400 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
:::

2. Create a high token usage alarm:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch put-metric-alarm \
  --alarm-name "Codex-HighTokenUsage" \
  --alarm-description "Alert when approaching token rate limits" \
  --metric-name "codex.token.usage" \
  --namespace "Codex" \
  --statistic Sum \
  --period 3600 \
  --threshold 1000000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
:::

3. Verify the alarms are configured in the [CloudWatch Alarms console](https://console.aws.amazon.com/cloudwatch/home#alarmsV2).

## 5. Next steps

With metrics collection configured, you can:
- Deploy the monitoring dashboard for visualization
- Set up analytics pipelines for historical analysis
- Configure quota monitoring for cost management
- Create custom dashboards for different stakeholders
