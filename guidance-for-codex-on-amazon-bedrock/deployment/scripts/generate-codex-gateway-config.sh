#!/usr/bin/env bash
# Generate a developer bundle for the LiteLLM Gateway path.
# Writes install.sh / uninstall.sh / README.md / config.toml fragment
# into the output directory for distribution to developers.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: generate-codex-gateway-config.sh [options]

Required:
  --gateway-url URL       Full gateway endpoint (e.g. https://gw.example.com/v1)

Optional:
  --key-mint-url URL      Self-service key endpoint (e.g. https://gw/sso/key/generate)
  --model ID              Default model alias (default: openai.gpt-5.4)
  --profile-name NAME     Codex profile name (default: codex-gateway)
  --enable-local-otel     Enable local OTEL collector configuration
  --aws-region REGION     AWS region for OTEL (required if --enable-local-otel)
  --user-email EMAIL      User email for attribution (required if --enable-local-otel)
  --outdir DIR            Output directory (default: ./codex-gateway-config)
USAGE
}

GATEWAY_URL=""
KEY_MINT_URL=""
MODEL="openai.gpt-5.4"
PROFILE_NAME="codex-gateway"
OUTDIR="./codex-gateway-config"
ENABLE_LOCAL_OTEL="false"
AWS_REGION=""
USER_EMAIL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gateway-url) GATEWAY_URL="$2"; shift 2 ;;
    --key-mint-url) KEY_MINT_URL="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --profile-name) PROFILE_NAME="$2"; shift 2 ;;
    --enable-local-otel) ENABLE_LOCAL_OTEL="true"; shift ;;
    --aws-region) AWS_REGION="$2"; shift 2 ;;
    --user-email) USER_EMAIL="$2"; shift 2 ;;
    --outdir) OUTDIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$GATEWAY_URL" ]]; then
  echo "missing required flag: --gateway-url" >&2
  usage
  exit 2
fi

if [[ "$ENABLE_LOCAL_OTEL" == "true" ]]; then
  if [[ -z "$AWS_REGION" ]] || [[ -z "$USER_EMAIL" ]]; then
    echo "error: --enable-local-otel requires --aws-region and --user-email" >&2
    exit 2
  fi
fi

mkdir -p "$OUTDIR"

cat >"$OUTDIR/config.toml.fragment" <<'TOML'
# >>> codex-gateway managed: do not edit inside fences <<<
# Codex CLI configuration for LiteLLM Gateway
#
# IMPORTANT: You must set OPENAI_API_KEY environment variable
# AND update the http_headers below with your actual API key
TOML

cat >>"$OUTDIR/config.toml.fragment" <<TOML
model = "$MODEL"
model_provider = "litellm-gateway"

[model_providers.litellm-gateway]
name = "LiteLLM Gateway"
type = "openai"
base_url = "$GATEWAY_URL"
api_key = "env:OPENAI_API_KEY"
# REQUIRED: Codex CLI needs explicit Authorization header for custom providers
# Replace YOUR_API_KEY_HERE with your actual sk-litellm-... key
http_headers = { Authorization = "Bearer YOUR_API_KEY_HERE" }
# >>> end codex-gateway managed <<<
TOML

# Add OTEL configuration if enabled
if [[ "$ENABLE_LOCAL_OTEL" == "true" ]]; then
  cat >>"$OUTDIR/config.toml.fragment" <<TOML

# >>> codex-otel managed: do not edit inside fences <<<
# OpenTelemetry configuration for local metrics collection
[otel]
environment = "prod"
exporter = { otlp-http = {
  endpoint = "http://localhost:4318/v1/metrics",
  protocol = "binary"
}}
# >>> end codex-otel managed <<<
TOML
fi

cat >"$OUTDIR/install.sh" <<'INSTALL'
#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cfg="$HOME/.codex/config.toml"
mkdir -p "$HOME/.codex"
touch "$cfg"

# Check if API key needs to be set
fragment="$here/config.toml.fragment"
if grep -q "YOUR_API_KEY_HERE" "$fragment"; then
  echo "════════════════════════════════════════════════════════════"
  echo "Codex CLI - API Key Setup"
  echo "════════════════════════════════════════════════════════════"
  echo ""
  echo "Enter your LiteLLM Gateway API key (starts with sk-litellm-):"
  echo "(Input will be hidden for security)"
  echo ""
  read -s -p "API Key: " API_KEY
  echo ""

  # Validate format
  if [[ ! "$API_KEY" =~ ^sk- ]]; then
    echo ""
    echo "❌ Invalid API key format. Key should start with 'sk-'"
    echo "   Please run ./install.sh again with the correct key."
    exit 1
  fi

  # Update the config fragment with the actual key
  sed "s|YOUR_API_KEY_HERE|$API_KEY|g" "$fragment" > "$fragment.tmp"
  mv "$fragment.tmp" "$fragment"

  echo "✓ API key configured"
  echo ""
fi

# Strip any prior managed blocks (both codex-gateway and codex-otel), then append.
awk '/# >>> end (codex-gateway|codex-otel) managed/{skip=0; next} /# >>> (codex-gateway|codex-otel) managed/{skip=1} !skip{print}' "$cfg" >"$cfg.tmp"
mv "$cfg.tmp" "$cfg"
# Ensure trailing newline so the next awk pass can match the fence on its own line.
[[ -s "$cfg" && $(tail -c1 "$cfg") != "" ]] && printf '\n' >>"$cfg"
cat "$here/config.toml.fragment" >>"$cfg"

echo "✓ Wrote configuration to $cfg"

# Remove OpenAI auth.json to prevent conflicts
if [[ -f "$HOME/.codex/auth.json" ]]; then
  mv "$HOME/.codex/auth.json" "$HOME/.codex/auth.json.backup.$(date +%s)"
  echo "✓ Backed up existing auth.json (was pointing to api.openai.com)"
fi

# Install OTEL collector if present
if [[ -f "$here/otelcol-local" ]]; then
  echo ""
  echo "Installing OTEL collector..."
  mkdir -p "$HOME/.codex/otel"

  cp "$here/otelcol-local" "$HOME/.codex/otel/"
  cp "$here/otel-config.yaml" "$HOME/.codex/otel/"
  cp "$here/start-collector.sh" "$HOME/.codex/otel/"
  cp "$here/stop-collector.sh" "$HOME/.codex/otel/"
  cp "$here/collector-status.sh" "$HOME/.codex/otel/"

  chmod +x "$HOME/.codex/otel/otelcol-local"
  chmod +x "$HOME/.codex/otel"/*.sh

  # Remove quarantine on macOS
  if [[ "$OSTYPE" == "darwin"* ]]; then
    xattr -d com.apple.quarantine "$HOME/.codex/otel/otelcol-local" 2>/dev/null || true
  fi

  echo "✓ OTEL collector installed to ~/.codex/otel/"

  # Start collector
  "$HOME/.codex/otel/start-collector.sh"
  echo "✓ OTEL collector started"
fi

# Detect shell and add alias
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]]; then
  SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
  SHELL_RC="$HOME/.bashrc"
fi

MODEL="$(grep '^model ' "$fragment" | head -1 | sed 's/^model = "\(.*\)"/\1/')"
MODEL="${MODEL:-openai.gpt-5.4}"

if [[ -n "$SHELL_RC" ]]; then
  if ! grep -q "alias codex-gateway=" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Codex CLI alias for LiteLLM Gateway" >> "$SHELL_RC"
    echo 'alias codex-gateway='"'"'codex -c model_provider="litellm-gateway" -c model="'"$MODEL"'"'"'"'' >> "$SHELL_RC"
    echo "✓ Added 'codex-gateway' alias to $SHELL_RC"
  else
    echo "✓ Alias 'codex-gateway' already exists in $SHELL_RC"
  fi
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Installation Complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Reload your shell: source $SHELL_RC"
echo "  2. Test Codex CLI: codex-gateway exec 'Say hello'"
if [[ -f "$here/otelcol-local" ]]; then
  echo "  3. Check OTEL: ~/.codex/otel/collector-status.sh"
fi
echo ""
echo "See README.md for detailed usage and troubleshooting."
echo "════════════════════════════════════════════════════════════"
INSTALL
chmod +x "$OUTDIR/install.sh"

cat >"$OUTDIR/uninstall.sh" <<'UNINSTALL'
#!/usr/bin/env bash
set -euo pipefail
cfg="$HOME/.codex/config.toml"
[[ -f "$cfg" ]] || exit 0
awk '/# >>> end codex-gateway managed/{skip=0; next} /# >>> codex-gateway managed/{skip=1} !skip{print}' "$cfg" >"$cfg.tmp"
mv "$cfg.tmp" "$cfg"
echo "✓ Removed managed block from $cfg"

# Remove alias from shell rc files
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
  if [[ -f "$rc" ]] && grep -q "alias codex-gateway=" "$rc"; then
    # Remove the alias line and the comment line above it
    sed -i.bak '/# Codex CLI alias for LiteLLM Gateway/d; /alias codex-gateway=/d' "$rc"
    echo "✓ Removed 'codex-gateway' alias from $rc"
  fi
done

# Restore auth.json if it was backed up
if [[ -f "$HOME/.codex/auth.json.backup."* ]]; then
  latest_backup=$(ls -t "$HOME/.codex/auth.json.backup."* | head -1)
  mv "$latest_backup" "$HOME/.codex/auth.json"
  echo "✓ Restored auth.json from backup"
fi

echo ""
echo "Uninstall complete. Restart your shell to apply changes."
UNINSTALL
chmod +x "$OUTDIR/uninstall.sh"

KEY_SECTION="Ask your platform team for a per-user key."
if [[ -n "$KEY_MINT_URL" ]]; then
  KEY_SECTION=$(cat <<MINT
Self-service via IdP SSO:

\`\`\`bash
open "$KEY_MINT_URL"
# Copy the sk-... key the page returns, then:
export OPENAI_API_KEY="sk-..."
\`\`\`
MINT
)
fi

cat >"$OUTDIR/README.md" <<'README'
# Codex on Bedrock - Developer Bundle

Get your API key from your admin before running the installer.

## Quick Start

```bash
# 1. Run installer (will prompt for API key)
./install.sh

# 2. Reload shell
source ~/.zshrc  # or ~/.bashrc

# 3. Test
codex-gateway exec "What is 2+2?"
```

## What's Included

- `install.sh` - Interactive installer (prompts for API key)
- `uninstall.sh` - Removes configuration
- `config.toml.fragment` - Codex CLI configuration
- `README.md` - This file

## Installation Details

When you run `./install.sh`, it will:

1. **Prompt for your API key** (get this from your admin)
2. Configure `~/.codex/config.toml` with LiteLLM Gateway settings
3. Add `codex-gateway` alias to your shell profile
4. Remove any conflicting OpenAI authentication

Your API key will be embedded in the config for Codex CLI to work properly.

## Configuration Explained

The installer creates this configuration in `~/.codex/config.toml`:

```toml
# Default model and provider
model = "gpt-4o"
model_provider = "litellm-gateway"

# Custom provider definition
[model_providers.litellm-gateway]
name = "LiteLLM Gateway"              # Display name
type = "openai"                       # OpenAI-compatible API
base_url = "http://your-gateway/v1"   # Your gateway endpoint
api_key = "env:OPENAI_API_KEY"        # For curl/API access (reads from environment)
http_headers = { Authorization = "Bearer sk-..." }  # For Codex CLI (embedded key)
```

**Why two API key fields?**

- `api_key = "env:OPENAI_API_KEY"` → Used by curl and OpenAI SDK (reads from `$OPENAI_API_KEY`)
- `http_headers = { Authorization = "..." }` → Used by Codex CLI (embedded directly)

**Why is `http_headers` needed?**

Codex CLI has a bug where it doesn't automatically send the API key for custom providers.
Setting it explicitly in `http_headers` works around this limitation.

## Usage

### Option 1: Codex CLI (Recommended)

```bash
# Use the alias (automatically configured)
codex-gateway exec "Write a Python hello world function"

# Interactive mode
codex-gateway

# Or use full command
codex -c 'model_provider="litellm-gateway"' -c 'model="gpt-4o"' exec "your prompt"
```

### Option 2: Direct API (curl)

```bash
# Set environment variable
export OPENAI_API_KEY="sk-litellm-your-key-here"

# Make API call
curl -X POST "http://your-gateway/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Verification

Check that Codex is using your gateway:

```bash
codex-gateway exec "test" 2>&1 | grep -E "(model|provider)"

# Should show:
# model: gpt-4o
# provider: litellm-gateway
```

If it shows `provider: openai`, you're connecting to api.openai.com instead of your gateway!

## Troubleshooting

### Issue: "401 Unauthorized" or "No api key passed in"

**Cause:** API key not properly configured

**Fix:**
```bash
# Check your config
cat ~/.codex/config.toml | grep -A 6 "litellm-gateway"

# Verify http_headers line has your actual key (not placeholder)
# Should see: http_headers = { Authorization = "Bearer sk-litellm-..." }

# If it shows YOUR_API_KEY_HERE, run install again:
./install.sh
```

### Issue: "Not inside a trusted directory"

**Cause:** Running from a non-git directory

**Fix:**
```bash
# Option 1: Run from a git repository
cd ~/your-project-with-git

# Option 2: Skip the check
codex-gateway exec --skip-git-repo-check "your prompt"
```

### Issue: Plain `codex` shows OpenAI sign-in

**Cause:** You ran `codex` without the alias or flags

**Fix:** Always use `codex-gateway` or the full command with flags:
```bash
codex-gateway exec "test"  # ✓ Correct
codex exec "test"           # ✗ Wrong - connects to OpenAI
```

## Getting Help

- See docs/QUICKSTART_LLM_GATEWAY.md in the main repository for detailed documentation
- Contact your platform team for API key issues
- For gateway access issues, verify your IP is in the allowed CIDR range

## Uninstall

```bash
./uninstall.sh
```

This removes:
- Managed block from `~/.codex/config.toml`
- `codex-gateway` alias from shell profile
- Restores any backed-up `auth.json` file
README

# Replace placeholders with actual values
sed "s|http://your-gateway/v1|$GATEWAY_URL|g" "$OUTDIR/README.md" > "$OUTDIR/README.md.tmp"
mv "$OUTDIR/README.md.tmp" "$OUTDIR/README.md"

# Copy refresh script if it exists
REFRESH_SCRIPT="$(dirname "$0")/../../source/refresh-codex-key.sh"
if [[ -f "$REFRESH_SCRIPT" ]]; then
  cp "$REFRESH_SCRIPT" "$OUTDIR/refresh-key.sh"
  chmod +x "$OUTDIR/refresh-key.sh"

  # Update GATEWAY_URL in the script
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|GATEWAY_URL=\${GATEWAY_URL:-.*}|GATEWAY_URL=\${GATEWAY_URL:-${GATEWAY_URL%/v1}}|g" "$OUTDIR/refresh-key.sh"
  else
    sed -i "s|GATEWAY_URL=\${GATEWAY_URL:-.*}|GATEWAY_URL=\${GATEWAY_URL:-${GATEWAY_URL%/v1}}|g" "$OUTDIR/refresh-key.sh"
  fi
fi

echo "Wrote $OUTDIR/"
ls -1 "$OUTDIR"
