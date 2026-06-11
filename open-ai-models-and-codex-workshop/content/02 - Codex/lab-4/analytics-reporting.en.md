---
title: "(Optional) Enable analytics and reporting"
weight: 45
---

Beyond real-time monitoring, you can deploy analytics pipelines for advanced reporting and historical analysis of Codex usage patterns.

## 1. Analytics architecture

The analytics pipeline creates a data lake for long-term metric storage and analysis:

1. **CloudWatch Logs** stream metrics to S3 using Kinesis Data Firehose.
2. **S3 Data Lake** stores metrics in Parquet format for efficient querying.
3. **AWS Athena** provides SQL query capabilities over metrics data.
4. **Automated archival** moves older data to Glacier for cost-effective storage.

## 2. Setting up the analytics pipeline

1. Create an S3 bucket for analytics data:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://codex-analytics-${ACCOUNT_ID}
:::

2. Create a Kinesis Data Firehose delivery stream:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws firehose create-delivery-stream \
  --delivery-stream-name codex-metrics-stream \
  --delivery-stream-type DirectPut \
  --s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::'${ACCOUNT_ID}':role/FirehoseRole",
    "BucketARN": "arn:aws:s3:::codex-analytics-'${ACCOUNT_ID}'",
    "Prefix": "metrics/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
    "ErrorOutputPrefix": "errors/"
  }'
:::

:::alert{type=info header="IAM role required"}
This command requires a Firehose IAM role with S3 write permissions. Create the role first if it doesn't exist.
:::

## 3. Running analytics queries with Athena

### Create an Athena table

1. Navigate to [AWS Athena](https://console.aws.amazon.com/athena/home) in the AWS Console.

2. Create a table for Codex metrics:

:::code{showCopyAction="true" language="sql" copyAutoReturn="true"}
CREATE EXTERNAL TABLE codex_metrics (
    timestamp bigint,
    user_id string,
    user_email string,
    department string,
    team_id string,
    session_id string,
    token_usage bigint,
    cost_usage double,
    lines_of_code int
)
PARTITIONED BY (year string, month string, day string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
LOCATION 's3://codex-analytics-ACCOUNT_ID/metrics/'
:::

### Example: Top users by token usage

:::code{showCopyAction="true" language="sql" copyAutoReturn="true"}
SELECT
    user_email,
    SUM(token_usage) as total_tokens,
    COUNT(DISTINCT session_id) as session_count,
    ROUND(SUM(cost_usage), 2) as total_cost
FROM codex_metrics
WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
GROUP BY user_email
ORDER BY total_tokens DESC
LIMIT 10;
:::

### Example: Usage by department

:::code{showCopyAction="true" language="sql" copyAutoReturn="true"}
SELECT
    department,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as total_sessions,
    SUM(token_usage) as total_tokens,
    ROUND(SUM(cost_usage), 2) as total_cost
FROM codex_metrics
WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
GROUP BY department
ORDER BY total_tokens DESC;
:::

## 4. Data retention and cost optimization

Configure lifecycle policies for cost-effective storage:

:::code{showCopyAction="true" language="json"}
{
  "Rules": [
    {
      "ID": "TransitionToGlacier",
      "Status": "Enabled",
      "Filter": {"Prefix": "metrics/"},
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "ID": "ExpireOldData",
      "Status": "Enabled",
      "Filter": {"Prefix": "metrics/"},
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
:::

## 5. Advanced analytics use cases

### ROI measurement

Calculate return on investment by comparing:
- Developer time saved (active time metrics)
- Code productivity gains (lines of code, commits)
- Cost of Codex usage

### Usage forecasting

Use historical data to:
- Predict future token consumption
- Plan capacity and budgets
- Identify seasonal usage patterns

## 6. Next steps

With analytics deployed, you can:
- Create automated reports for stakeholders
- Set up data-driven alerts and notifications
- Integrate with business intelligence tools
- Build custom applications using the analytics API
