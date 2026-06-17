ARG LITELLM_VERSION=main-latest
FROM ghcr.io/berriai/litellm:${LITELLM_VERSION}

# Install OpenTelemetry SDK for metrics export
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http

RUN useradd --create-home --uid 10001 --shell /bin/false appuser \
    && mkdir -p /app \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser litellm_config.yaml /app/config.yaml

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health/liveliness', timeout=5)" || exit 1
