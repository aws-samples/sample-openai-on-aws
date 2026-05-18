#!/usr/bin/env bash
# Cleanup script to remove OpenAI credentials and ensure Codex only uses LiteLLM Gateway
set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "Codex CLI Cleanup - Remove OpenAI Credentials"
echo "════════════════════════════════════════════════════════════════"
echo ""

CODEX_DIR="$HOME/.codex"

# 1. Backup and remove auth.json (contains OpenAI credentials)
if [[ -f "$CODEX_DIR/auth.json" ]]; then
  backup_name="$CODEX_DIR/auth.json.backup.$(date +%s)"
  mv "$CODEX_DIR/auth.json" "$backup_name"
  echo "✓ Backed up auth.json to: $backup_name"
  echo "  (This file was connecting to api.openai.com)"
else
  echo "✓ No auth.json found (already clean)"
fi

# 2. Remove any OPENAI_API_BASE environment variables from shell profiles
for rc_file in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
  if [[ -f "$rc_file" ]]; then
    if grep -q "OPENAI_API_BASE" "$rc_file" 2>/dev/null; then
      # Backup first
      cp "$rc_file" "$rc_file.backup.$(date +%s)"
      # Remove lines containing OPENAI_API_BASE
      grep -v "OPENAI_API_BASE" "$rc_file" > "$rc_file.tmp" && mv "$rc_file.tmp" "$rc_file"
      echo "✓ Removed OPENAI_API_BASE from: $rc_file"
    fi
  fi
done

# 3. Check config.toml for litellm-gateway provider
if [[ -f "$CODEX_DIR/config.toml" ]]; then
  if grep -q "model_provider = \"litellm-gateway\"" "$CODEX_DIR/config.toml"; then
    echo "✓ config.toml is configured for litellm-gateway"
  else
    echo "⚠️  config.toml does NOT have litellm-gateway configured"
    echo "   Run ./install.sh from your codex-bundle to set it up"
  fi
else
  echo "⚠️  No config.toml found - run ./install.sh from your codex-bundle"
fi

# 4. Verify OPENAI_API_KEY is NOT your personal OpenAI key
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Verification Steps"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Check your OPENAI_API_KEY:"
echo "   echo \$OPENAI_API_KEY"
echo ""
echo "   Should start with: sk-litellm-... (NOT sk-proj-... or other OpenAI keys)"
echo ""
echo "2. Test Codex CLI:"
echo "   codex-gateway exec \"Say hi\" 2>&1 | grep provider"
echo ""
echo "   Should show: provider: litellm-gateway"
echo ""
echo "3. If it shows 'provider: openai', you're still using OpenAI's API!"
echo "   Fix: Run ./install.sh from your codex-bundle"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "Cleanup Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Reload your shell: source ~/.zshrc (or ~/.bashrc)"
echo "  2. Verify: codex-gateway exec \"test\" 2>&1 | head -15"
echo "  3. You should see 'provider: litellm-gateway'"
echo ""
