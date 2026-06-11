---
title: "Set up the Codex App for Bedrock"
weight: 11
---

The Codex App is a graphical interface for working with Codex: a chat surface, a built-in terminal, richer diff views, and a visual home for skills, worktrees, automations, and parallel tasks. This page points the App at the GPT models you set up on Amazon Bedrock in Getting Started.

:::alert{type="info" header="How Codex talks to Bedrock"}
Codex has a built-in `amazon-bedrock` provider. You set it once in `~/.codex/config.toml` and Codex routes model requests to Bedrock using AWS-native authentication. There is no ChatGPT sign-in and no `OPENAI_API_KEY` for the Bedrock path. See OpenAI's [Codex on Amazon Bedrock](https://developers.openai.com/codex/amazon-bedrock) guide for the full reference.
:::

## 1. Install the Codex App

1. Download the Codex App from [openai.com/codex](https://openai.com/codex/), or run:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex app
:::

This launches the App if it is installed, or opens the installer page.

![Codex Desktop App installer](/static/images/codex/lab-1/codex-app-install.png)

## 2. Point Codex at Bedrock

1. Create the Codex config and select the Bedrock provider and workshop model:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
mkdir -p ~/.codex
cat >> ~/.codex/config.toml << 'EOF'
model = "openai.gpt-5.4"
model_provider = "amazon-bedrock"
web_search = "disabled"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
EOF
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex" | Out-Null
@"
model = "openai.gpt-5.4"
model_provider = "amazon-bedrock"
web_search = "disabled"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
"@ | Add-Content "$env:USERPROFILE\.codex\config.toml"
:::
::::
:::::

The `openai.` model prefix is required on Bedrock. `web_search = "disabled"` because Bedrock does not serve the hosted web-search tool.

2. The App does not inherit your terminal's environment, so give it credentials through `~/.codex/.env`. Write your Bedrock bearer token (the same kind you minted in Getting Started) and region into that file:

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

3. Restart the Codex App so it picks up the config and the `.env` file.

:::alert{type="info" header="Tokens expire"}
The Bedrock bearer token is valid for roughly 12 hours. If the App starts returning `401` errors, re-run the command above to write a fresh token into `~/.codex/.env`, then restart the App.
:::

4. Open **Settings** (gear icon or `Cmd+,`) and confirm the model is `openai.gpt-5.4` and the provider is `amazon-bedrock`.

![Codex App Settings](/static/images/codex/lab-1/codex-app-settings.png)

## 3. First App exercise: open the workshop project

1. Open the project folder with **File > Open Folder** or `Cmd+O`, and select:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
~/workshop/sample-openai-on-aws/bedrock-chat
:::

2. Ask Codex to build initial context:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Analyze this repository and summarize:
- What the project does
- The main entry points and important folders
- How to run tests or local development
- The files you would inspect first before making a change
:::

3. Ask a concrete follow-up:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Based on that overview, what is the safest small change we could make to validate the development workflow?
:::

A normal answer confirms the App is talking to GPT on Bedrock.

## 4. Using the App

### Chat interface

The main interface is a chat window where you prompt Codex with questions, coding tasks, or file operations.

![Codex App chat interface](/static/images/codex/lab-1/codex-app-chat.png)

### Built-in terminal

The App includes an embedded terminal that Codex uses to run shell commands:

1. Click the **Terminal** icon in the top-right corner of the window.

2. Choose to open the terminal at the **bottom** or on the **right** side of the screen.

![Open Codex terminal](/static/images/codex/lab-1/create-codex-app-terminal.png)

3. The terminal shows every command Codex executes, with output. You can also type commands directly.

![Codex App terminal](/static/images/codex/lab-1/codex-app-terminal.png)

### Working with projects

1. Open a project folder with **File > Open Folder** or `Cmd+O`.

2. For this workshop, use `~/workshop/sample-openai-on-aws/bedrock-chat`. Codex detects the project structure and loads any `AGENTS.md` file in the root.

3. Use the chat to ask about the project, request changes, or run tasks.

:::alert{type="info" header="Same capabilities as the CLI"}
The App supports the same features as the CLI: file reading and writing, shell execution, sandbox policies, and approval workflows. The difference is the visual interface. A few cloud-dependent features (web search, image generation, Codex cloud tasks) are unavailable on the Bedrock path.
:::

## 5. Congratulations!

You've pointed the Codex App at GPT on Amazon Bedrock, opened the workshop repo, and asked Codex to build working context. The next page sets up the same thing for the CLI.
