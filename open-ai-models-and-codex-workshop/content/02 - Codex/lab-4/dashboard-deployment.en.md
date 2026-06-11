---
title: "Deploy usage dashboard"
weight: 44
---

This section shows you how to deploy a comprehensive Codex monitoring dashboard that provides real-time visibility into usage patterns and performance metrics.

## 1. Dashboard overview

A Codex monitoring dashboard provides comprehensive visibility into usage patterns and performance metrics:

<!-- TODO: Create Codex-specific dashboard screenshot showing:
     - Total Tokens Used
     - Active Users
     - Operations Count
     - Cache Efficiency
     - Token Usage by Model Over Time
     - Developer Productivity Metrics
     Reference: /static/images/codex/ClaudeCodeDashboard.png (Claude-specific, needs Codex equivalent)
-->

The dashboard includes usage metrics, user analytics, and API monitoring across your Codex deployment.

## 2. Create a CloudWatch dashboard

1. Create a basic monitoring dashboard:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch put-dashboard \
  --dashboard-name "CodexMonitoring" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
          "title": "Token Usage Over Time",
          "view": "timeSeries",
          "stacked": false,
          "metrics": [
            ["Codex", "codex.token.usage", {"stat": "Sum", "period": 3600}]
          ],
          "region": "us-east-2"
        }
      },
      {
        "type": "metric",
        "x": 12,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
          "title": "Session Count",
          "view": "timeSeries",
          "stacked": false,
          "metrics": [
            ["Codex", "codex.session.count", {"stat": "Sum", "period": 3600}]
          ],
          "region": "us-east-2"
        }
      },
      {
        "type": "metric",
        "x": 0,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
          "title": "Cost Usage",
          "view": "timeSeries",
          "stacked": false,
          "metrics": [
            ["Codex", "codex.cost.usage", {"stat": "Sum", "period": 3600}]
          ],
          "region": "us-east-2"
        }
      },
      {
        "type": "metric",
        "x": 12,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
          "title": "Lines of Code Modified",
          "view": "timeSeries",
          "stacked": false,
          "metrics": [
            ["Codex", "codex.lines_of_code.count", {"stat": "Sum", "period": 3600}]
          ],
          "region": "us-east-2"
        }
      }
    ]
  }'
:::

## 3. Accessing the dashboard

To access your deployed dashboard:

1. Get the dashboard URL:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=CodexMonitoring"
:::

2. Navigate to the URL in your web browser to view the dashboard.

## 4. Add custom widgets

You can customize your dashboard with additional widgets:

### User activity widget

:::code{showCopyAction="true" language="json"}
{
  "type": "log",
  "x": 0,
  "y": 12,
  "width": 24,
  "height": 6,
  "properties": {
    "title": "Recent User Activity",
    "query": "SOURCE '/aws/codex/metrics' | fields @timestamp, user.id, codex.token.usage | sort @timestamp desc | limit 20",
    "region": "us-east-2"
  }
}
:::

### Cost by department widget

:::code{showCopyAction="true" language="json"}
{
  "type": "log",
  "x": 0,
  "y": 18,
  "width": 12,
  "height": 6,
  "properties": {
    "title": "Cost by Department",
    "query": "SOURCE '/aws/codex/metrics' | stats sum(codex.cost.usage) as total_cost by department | sort total_cost desc",
    "region": "us-east-2"
  }
}
:::

## 5. Dashboard best practices

| Practice | Description |
|----------|-------------|
| Time range selection | Use consistent time ranges for comparable metrics |
| Refresh interval | Set automatic refresh for real-time monitoring |
| Annotations | Add annotations for significant events |
| Sharing | Create read-only shares for stakeholders |

## 6. Next steps

With the dashboard deployed, you can:
- Monitor real-time Codex usage across your organization
- Analyze historical trends and patterns
- Set up alerts based on dashboard metrics
- Deploy analytics pipelines for advanced reporting
