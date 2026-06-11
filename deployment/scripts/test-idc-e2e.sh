#!/usr/bin/env bash
# Sandbox-only E2E test for the IdC deploy path.
#
# Runs install.sh from a generator-produced bundle, forces a cold auth state,
# and smoke-tests Bedrock Converse via the installed credential_process profile.
# Prints time-to-first-successful-Bedrock-call.
#
# NOT distributed to end users. Run this on a workstation (not the control
# host) — it needs a browser for IdC sign-in.
#
# Usage: test-idc-e2e.sh <path-to-generated-bundle-dir>

set -uo pipefail

BUNDLE="${1:-}"
[[ -z "$BUNDLE" || ! -d "$BUNDLE" ]] && { echo "usage: $0 <bundle-dir>" >&2; exit 2; }

PROFILE="codex-bedrock"
SSO_SESSION="codex-bedrock"
REGION="us-west-2"
MODEL_ID="openai.gpt-oss-120b-1:0"

log()  { printf '\n\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
fail() { printf '\n\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

log "Running installer from bundle: $BUNDLE"
"$BUNDLE/install.sh" || fail "installer failed"

log "Forcing cold auth state"
aws sso logout 2>/dev/null || true
rm -rf ~/.aws/sso/cache ~/.aws/cli/cache
ok "SSO cache cleared"

log "Invoking credential chain (browser should pop automatically)"
START=$(date +%s)
aws sts get-caller-identity --profile "$PROFILE" || fail "credential_process did not resolve"

log "Bedrock Converse smoke test against $MODEL_ID in $REGION"
RESP="$(mktemp)"
if aws bedrock-runtime converse \
    --profile "$PROFILE" --region "$REGION" \
    --model-id "$MODEL_ID" \
    --messages '[{"role":"user","content":[{"text":"Reply with the single word: OK"}]}]' \
    > "$RESP" 2>&1; then
  END=$(date +%s)
  ok "Bedrock call succeeded"
  head -c 600 "$RESP"; echo
  printf '\n\033[1;32mtime-to-first-successful-Bedrock-call: %ss\033[0m\n' "$((END - START))"
else
  cat "$RESP"
  fail "Bedrock Converse failed"
fi

echo
echo "Verify Codex client separately:"
echo "  codex   # send a prompt; should work with no manual login"
echo "  # To test expiry: 'aws sso logout' in another terminal, send a new Codex prompt — browser should pop."
