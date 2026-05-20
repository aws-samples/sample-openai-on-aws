#!/usr/bin/env bash
# Download OpenTelemetry Collector binaries for local deployment
# Uses OpenTelemetry Contrib Collector (supports all platforms)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARIES_DIR="$SCRIPT_DIR/../binaries"
OTEL_VERSION="${OTEL_VERSION:-0.111.0}"

usage() {
  cat <<EOF
Usage: build-local-collector.sh [options]

Downloads OpenTelemetry Collector binaries for local deployment.

Options:
  --version VERSION    OTEL collector version (default: $OTEL_VERSION)
  --platform PLATFORM  Build single platform: darwin-arm64, darwin-amd64, linux-amd64
  --all               Build all platforms (default)
  -h, --help          Show this help

Examples:
  ./build-local-collector.sh --platform darwin-arm64
  ./build-local-collector.sh --all
EOF
}

PLATFORMS=()
BUILD_ALL=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) OTEL_VERSION="$2"; shift 2;;
    --platform) PLATFORMS+=("$2"); BUILD_ALL=false; shift 2;;
    --all) BUILD_ALL=true; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if [[ "$BUILD_ALL" == "true" ]]; then
  PLATFORMS=("darwin-arm64" "darwin-amd64" "linux-amd64")
fi

mkdir -p "$BINARIES_DIR"

log() { echo "[$(date +%H:%M:%S)] $*"; }
ok() { echo "[$(date +%H:%M:%S)] ✓ $*"; }

BASE_URL="https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download"

download_binary() {
  local platform=$1
  local output_name="otelcol-local-${platform}"

  case "$platform" in
    darwin-arm64)
      url="$BASE_URL/v${OTEL_VERSION}/otelcol-contrib_${OTEL_VERSION}_darwin_arm64.tar.gz"
      ;;
    darwin-amd64)
      url="$BASE_URL/v${OTEL_VERSION}/otelcol-contrib_${OTEL_VERSION}_darwin_amd64.tar.gz"
      ;;
    linux-amd64)
      url="$BASE_URL/v${OTEL_VERSION}/otelcol-contrib_${OTEL_VERSION}_linux_amd64.tar.gz"
      ;;
    *)
      echo "Unsupported platform: $platform" >&2
      return 1
      ;;
  esac

  log "Downloading $platform from GitHub releases"

  local tmpdir=$(mktemp -d)
  if curl -fSL "$url" -o "$tmpdir/otelcol.tar.gz"; then
    tar -xzf "$tmpdir/otelcol.tar.gz" -C "$tmpdir"
    mv "$tmpdir/otelcol-contrib" "$BINARIES_DIR/$output_name"
    chmod +x "$BINARIES_DIR/$output_name"
    rm -rf "$tmpdir"

    size=$(du -h "$BINARIES_DIR/$output_name" | cut -f1)
    ok "Downloaded $output_name ($size)"
  else
    echo "Failed to download $platform" >&2
    rm -rf "$tmpdir"
    return 1
  fi
}

log "Downloading OpenTelemetry Collector v$OTEL_VERSION"
log "Output directory: $BINARIES_DIR"

for platform in "${PLATFORMS[@]}"; do
  download_binary "$platform"
done

ok "All binaries downloaded successfully"
ok "Binaries available in: $BINARIES_DIR"

cat <<EOF

Next steps:
  1. Run 'cxwb distribute' to create developer bundles
  2. Bundles will include appropriate binary for each platform

Available binaries:
EOF

ls -lh "$BINARIES_DIR"/otelcol-local-* 2>/dev/null || echo "  (none yet)"
