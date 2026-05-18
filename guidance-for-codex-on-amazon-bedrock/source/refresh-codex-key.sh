#!/bin/bash
# Auto-refresh Codex API key via OIDC self-service portal
# Usage: ./refresh-codex-key.sh
#
# This script helps developers refresh their API key when it expires
# (if your admin configured key expiration)

set -e

# Configuration
GATEWAY_URL="${GATEWAY_URL:-https://your-gateway-url}"  # Override with your actual gateway URL
PROFILE_FILE="${SHELL_PROFILE:-$HOME/.zshrc}"  # Change to .bashrc for Linux

# Detect shell profile
if [[ "$SHELL" == */bash ]]; then
    PROFILE_FILE="$HOME/.bashrc"
elif [[ "$SHELL" == */zsh ]]; then
    PROFILE_FILE="$HOME/.zshrc"
fi

echo "═══════════════════════════════════════════════════════════════"
echo "🔄 Codex API Key Refresh Utility"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Gateway: $GATEWAY_URL"
echo "Profile: $PROFILE_FILE"
echo ""

# Check if gateway URL is configured
if [[ "$GATEWAY_URL" == "https://your-gateway-url" ]]; then
    echo "❌ Gateway URL not configured!"
    echo ""
    echo "Set environment variable or edit this script:"
    echo "  export GATEWAY_URL=https://your-actual-gateway-url"
    echo "  ./refresh-codex-key.sh"
    exit 1
fi

# Step 1: Open OIDC portal
echo "Step 1: Opening OIDC self-service portal..."
echo ""

if command -v open &> /dev/null; then
    # macOS
    open "$GATEWAY_URL/sso/key/generate"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "$GATEWAY_URL/sso/key/generate"
else
    echo "Please open this URL manually:"
    echo "  $GATEWAY_URL/sso/key/generate"
fi

echo ""
echo "Browser should open and redirect to your corporate IdP"
echo "After authenticating, copy the API key from the portal"
echo ""

# Step 2: Prompt for new key
echo "Step 2: Paste your new API key"
echo "(Input is hidden for security)"
echo ""
read -s -p "New API key: " NEW_KEY
echo ""
echo ""

# Validate key format
if [[ ! $NEW_KEY =~ ^sk-litellm- ]]; then
    echo "❌ Invalid key format!"
    echo "Expected: sk-litellm-xxxxxxxxxxxxx"
    echo "Received: ${NEW_KEY:0:10}..."
    exit 1
fi

echo "✓ Key format valid"
echo ""

# Step 3: Update shell profile
echo "Step 3: Updating shell profile..."
echo ""

# Backup profile
cp "$PROFILE_FILE" "${PROFILE_FILE}.bak"
echo "  ✓ Backed up to ${PROFILE_FILE}.bak"

if grep -q "export OPENAI_API_KEY=" "$PROFILE_FILE"; then
    # Replace existing key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s|export OPENAI_API_KEY=.*|export OPENAI_API_KEY=$NEW_KEY|g" "$PROFILE_FILE"
    else
        # Linux sed
        sed -i "s|export OPENAI_API_KEY=.*|export OPENAI_API_KEY=$NEW_KEY|g" "$PROFILE_FILE"
    fi
    echo "  ✓ Updated existing OPENAI_API_KEY in $PROFILE_FILE"
else
    # Append new key
    echo "" >> "$PROFILE_FILE"
    echo "# Codex API Key (auto-updated by refresh-codex-key.sh)" >> "$PROFILE_FILE"
    echo "export OPENAI_API_KEY=$NEW_KEY" >> "$PROFILE_FILE"
    echo "  ✓ Added OPENAI_API_KEY to $PROFILE_FILE"
fi

# Step 4: Export for current shell
export OPENAI_API_KEY=$NEW_KEY
echo "  ✓ Exported to current shell"
echo ""

# Step 5: Test the key
echo "Step 4: Testing new API key..."
echo ""

TEST_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/v1/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"gpt-4o","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}' 2>&1)

if echo "$TEST_RESPONSE" | grep -q '"choices"'; then
    echo "✅ Success! API key is working"
    echo ""
    echo "Response preview:"
    echo "$TEST_RESPONSE" | head -c 200
    echo "..."
else
    echo "⚠️  Warning: Test request failed"
    echo ""
    echo "Response:"
    echo "$TEST_RESPONSE" | head -c 300
    echo ""
    echo "Key was updated in profile, but test failed."
    echo "Check gateway URL or try again later."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ API Key Refresh Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  • Restart your terminal or run: source $PROFILE_FILE"
echo "  • Launch Codex: codex"
echo ""
echo "If you have multiple terminals open, restart them to pick up the new key."
echo ""
