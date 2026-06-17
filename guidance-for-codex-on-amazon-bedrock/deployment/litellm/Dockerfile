ARG LITELLM_VERSION=main-latest
FROM ghcr.io/berriai/litellm:${LITELLM_VERSION}

# Install OpenTelemetry SDK for metrics export and the official Bedrock
# bearer-token generator used for long-lived Mantle auth.
RUN /usr/bin/python -m ensurepip --upgrade \
    && /usr/bin/python -m pip install --no-cache-dir \
    --target /app/.venv/lib/python3.13/site-packages \
    aws-bedrock-token-generator \
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
    mkdir -p /app /home/appuser/.cache/prisma-python; \
    if [ -d /root/.cache/prisma-python ]; then \
      cp -R /root/.cache/prisma-python/. /home/appuser/.cache/prisma-python/; \
    fi; \
    if [ -f /app/.venv/lib/python3.13/site-packages/prisma/client.py ]; then \
      sed -i 's#/root/.cache/prisma-python#/home/appuser/.cache/prisma-python#g' /app/.venv/lib/python3.13/site-packages/prisma/client.py; \
      rm -f /app/.venv/lib/python3.13/site-packages/prisma/__pycache__/client.cpython-313.pyc; \
    fi; \
    chown -R 10001:10001 /app /home/appuser

COPY --chown=10001:10001 litellm_config.yaml /app/config.yaml
COPY --chown=10001:10001 run_litellm_with_bedrock_mantle_refresh.py /app/run_litellm_with_bedrock_mantle_refresh.py
ENV HOME=/home/appuser
ENV XDG_CACHE_HOME=/home/appuser/.cache
ENV PRISMA_HOME_DIR=/home/appuser
USER appuser
ENTRYPOINT ["/app/.venv/bin/python", "/app/run_litellm_with_bedrock_mantle_refresh.py"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health/liveliness', timeout=5)" || exit 1
