---
title: "Configuring OpenTelemetry"
weight: 42
---

Codex supports OpenTelemetry to export metrics and events to monitoring backends. This section shows you how to configure telemetry collection for your Codex installation.

![OpenTelemetry Monitoring Flow](/static/images/codex/otel-monitoring-flow.png)

:::alert{type="warning" header="Telemetry configuration"}
Telemetry environment variables shown here follow standard OpenTelemetry conventions. The Codex-specific enable variable (`CODEX_ENABLE_TELEMETRY`) may have different naming in your version. Check Codex documentation for exact configuration.
:::

## 1. Quick start configuration

To configure OpenTelemetry using environment variables, follow these steps:

1. Enable telemetry collection:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export CODEX_ENABLE_TELEMETRY=1
:::

2. Configure exporters for testing:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_METRICS_EXPORTER=console
export OTEL_LOGS_EXPORTER=console
:::

3. Set shorter export intervals for debugging:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_METRIC_EXPORT_INTERVAL=10000  # 10 seconds
export OTEL_LOGS_EXPORT_INTERVAL=5000     # 5 seconds
:::

4. Run Codex to verify data collection:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex "hello world"
:::

5. Look for these key metrics:

- :code[codex.session.count]{showCopyAction=false}
- :code[codex.token.usage]{showCopyAction=false}
- :code[codex.cost.usage]{showCopyAction=false}

:::alert{type=info header="Console output for testing"}
The console exporter outputs metrics directly to your terminal, making it perfect for initial testing and understanding what data is being collected.
:::

## 2. OTLP configuration

For production environments, configure OTLP to send metrics to a collector:

1. Configure OTLP exporters:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
:::

2. Set protocol:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
:::

3. Set the endpoint to your OpenTelemetry Collector:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-alb-xxxxx.us-east-2.elb.amazonaws.com
:::

## 3. Configuration options

You can set custom organizational attributes via environment variables for cost allocation and team tracking:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export OTEL_RESOURCE_ATTRIBUTES="user.email=${USER}@example.com,user.id=$(whoami),department=engineering,team.id=platform,cost_center=eng-123,organization=mycompany"
:::

This enables you to:
- Filter metrics by team or department
- Track costs per cost center
- Create team-specific dashboards
- Set up alerts for specific teams

:::alert{type=warning header="Attribute formatting requirements"}
The :code[OTEL_RESOURCE_ATTRIBUTES]{showCopyAction=true} variable follows strict formatting rules:
- **No spaces allowed** in values
- Format: :code[key1=value1,key2=value2]{showCopyAction=true}
- Use underscores or camelCase instead of spaces
- Special characters must be percent-encoded
:::

## 4. Persist configuration

Add telemetry settings to your shell profile for persistence:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat >> ~/.bashrc << 'EOF'
# Codex telemetry configuration
export CODEX_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_RESOURCE_ATTRIBUTES="department=engineering,team.id=platform"
EOF
:::

## 5. Next steps

With OpenTelemetry configured, you can now:
- Set up metrics collection backends
- Create monitoring dashboards
- Configure alerting and notifications
- Deploy analytics pipelines for advanced reporting
