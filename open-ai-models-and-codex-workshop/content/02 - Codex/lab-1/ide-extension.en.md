---
title: "Optional: Install the IDE extension"
weight: 16
---

Install the Codex extension in VS Code or another supported editor for integrated AI assistance. Use this path if you prefer to stay inside your IDE; the App and CLI from the earlier pages remain available too.

## 1. Supported IDEs

Codex provides extensions for:

- VS Code
- Cursor
- Windsurf

## 2. Install in VS Code

1. Open VS Code and go to the Extensions view (:code[Ctrl+Shift+X]{showCopyAction=false}).

2. Search for "Codex" in the marketplace.

3. Click **Install** on the OpenAI Codex extension.

<!-- TODO: Create Codex VS Code extension screenshot (equivalent to Claude Code's vscode-claude-code-extension.png) -->
<!-- ![Codex VS Code extension](/static/images/codex/lab-1/codex-vscode-extension.png) -->

4. After installation, you'll see a Codex icon in the sidebar.

## 3. Configure the extension

The extension shares your :code[~/.codex/config.toml]{showCopyAction=false}, so the `amazon-bedrock` provider and model you set earlier apply automatically. Like the App, the extension may not inherit your shell environment, so it reads credentials from :code[~/.codex/.env]{showCopyAction=false}. If you set that file up on the App page, the extension is already covered. If not, write your Bedrock bearer token and region into it:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 -c "from aws_bedrock_token_generator import provide_token; print('AWS_BEARER_TOKEN_BEDROCK=' + provide_token(region='us-east-2'))" >> ~/.codex/.env
echo "AWS_REGION=us-east-2" >> ~/.codex/.env
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python -c "from aws_bedrock_token_generator import provide_token; print('AWS_BEARER_TOKEN_BEDROCK=' + provide_token(region='us-east-2'))" | Add-Content "$env:USERPROFILE\.codex\.env"
Add-Content "$env:USERPROFILE\.codex\.env" "AWS_REGION=us-east-2"
:::
::::
:::::

To verify the connection:

1. Restart your editor so the extension reloads :code[~/.codex/.env]{showCopyAction=false}.
2. Open the Codex sidebar panel and confirm it shows the `amazon-bedrock` provider and the `openai.gpt-5.4` model.

## 4. Using the extension

With the extension installed, you can:

- **Inline suggestions**: Get code completions as you type
- **Code actions**: Right-click to access Codex commands
- **Chat panel**: Open the Codex chat directly in VS Code
- **Selection context**: Select code and ask Codex about it

:::alert{type="info" header="CLI vs Extension"}
The CLI and extension share the same underlying Codex engine and the same `~/.codex/config.toml`. Use whichever interface fits your workflow, or both.
:::

## 5. Congratulations!

You've installed the Codex IDE extension and connected it to GPT on Amazon Bedrock.
