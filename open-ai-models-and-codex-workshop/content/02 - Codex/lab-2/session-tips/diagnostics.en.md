---
title: "Check status and diagnostics"
weight: 35
---

Monitor your Codex session and debug configuration issues.

## 1. Check session status

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/status
:::

Returns:
- Active model and provider
- Current approval policy
- Token usage (session/total)
- Active feature flags
- Loaded configuration files

## 2. Debug configuration

Print config layer precedence and diagnostics:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/debug-config
:::

This shows which config files are loaded and their order of precedence.

## 3. View git diff

Show uncommitted changes including untracked files:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/diff
:::

## 4. List MCP servers

View configured Model Context Protocol tools:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/mcp verbose
:::

## 5. Congratulations!

You can now diagnose and monitor your Codex sessions effectively.
