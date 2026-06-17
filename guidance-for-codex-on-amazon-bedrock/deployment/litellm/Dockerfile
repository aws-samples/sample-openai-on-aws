ARG LITELLM_VERSION=main-latest
FROM ghcr.io/berriai/litellm:${LITELLM_VERSION}

# Install OpenTelemetry SDK for metrics export
RUN pip install --no-cache-dir \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http

RUN set -eux; \
    if command -v useradd >/dev/null 2>&1; then \
      useradd --create-home --uid 10001 --shell /bin/false appuser; \
    elif adduser --help 2>&1 | grep -q BusyBox; then \
      adduser -S -D -H -u 10001 -h /home/appuser -s /bin/false appuser; \
    else \
      adduser --system --uid 10001 --home /home/appuser --shell /bin/false --disabled-login --gecos '' appuser; \
    fi; \
    mkdir -p /app; \
    chown -R 10001:10001 /app

COPY --chown=10001:10001 litellm_config.yaml /app/config.yaml

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health/liveliness', timeout=5)" || exit 1
