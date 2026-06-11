ARG LITELLM_VERSION=main-latest
FROM ghcr.io/berriai/litellm:${LITELLM_VERSION}

# Install OpenTelemetry SDK for metrics export
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http

COPY litellm_config.yaml /app/config.yaml
