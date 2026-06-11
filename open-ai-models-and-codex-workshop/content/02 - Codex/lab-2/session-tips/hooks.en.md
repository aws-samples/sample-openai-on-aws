---
title: "Automate workflows with hooks"
weight: 33
---

Hooks let you run custom scripts at specific points in Codex's lifecycle for automation and validation.

:::alert{type="warning" header="Hook configuration"}
Hook configuration syntax varies by Codex version. The examples below show common patterns - check your Codex documentation for exact syntax.
:::

## 1. View configured hooks

Use the help command to find hook-related commands:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/help
:::

## 2. Hook types

![Hooks Pipeline](/static/images/codex/lab-2/hooks-tools-pipeline.png)

| Hook | Trigger |
|:-----|:--------|
| :code[pre-prompt]{showCopyAction=false} | Before processing user input |
| :code[post-response]{showCopyAction=false} | After generating response |
| :code[pre-edit]{showCopyAction=false} | Before modifying files |
| :code[post-edit]{showCopyAction=false} | After modifying files |
| :code[pre-command]{showCopyAction=false} | Before executing shell commands |
| :code[post-command]{showCopyAction=false} | After executing shell commands |

Hooks intercept tool calls at specific points in the lifecycle:

![Hook Tool Identification](/static/images/codex/lab-2/hooks-identify-tools.png)

## 3. Configure hooks

Add hooks to your :code[~/.codex/config.toml]{showCopyAction=false} or project :code[.codex/config.toml]{showCopyAction=false}:

:::code{showCopyAction="true" language="toml"}
[hooks]
post-edit = ".codex/hooks/format.sh"
:::

## 4. Example: Auto-format after edits

Create a formatting hook:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p .codex/hooks
cat > .codex/hooks/format.sh << 'EOF'
#!/bin/bash
# Auto-format edited files
FILE_PATH=$1
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  npx prettier --write "$FILE_PATH"
fi
EOF
chmod +x .codex/hooks/format.sh
:::

:::alert{type="warning" header="Hook security"}
Hooks execute with your user permissions. Ensure hook scripts are from trusted sources.
:::

## 5. Congratulations!

You can now automate workflows with hooks for consistent, validated changes.
