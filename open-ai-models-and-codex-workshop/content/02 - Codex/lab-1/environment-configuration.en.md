---
title: "Set up the Codex CLI for Bedrock"
weight: 12
---

The CLI is the terminal-native Codex surface. Because Codex reads your shell environment, and Getting Started already left AWS credentials and `AWS_REGION=us-east-2` in your terminal, the CLI needs little more than a short config file to start running GPT on Amazon Bedrock.

:::alert{type="info" header="How Codex talks to Bedrock"}
Codex has a built-in `amazon-bedrock` provider. It authenticates with AWS-native credentials (your AWS profile or a Bedrock bearer token), not an `OPENAI_API_KEY`. See OpenAI's [Codex on Amazon Bedrock](https://developers.openai.com/codex/amazon-bedrock) guide for the full reference.
:::

## 1. Point Codex at Bedrock

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

2. Confirm the credentials Codex will use are present in this terminal. The `amazon-bedrock` provider checks for a Bedrock bearer token first, then falls back to the AWS credential chain:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
echo "Region: $AWS_REGION"
aws sts get-caller-identity
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
"Region: $($env:AWS_REGION)"
aws sts get-caller-identity
:::
::::
:::::

If `AWS_REGION` is empty or `get-caller-identity` fails, re-run the credential and region steps from Getting Started, then come back here.

:::alert{type="info" header="Two ways to authenticate"}
The commands above use your **AWS credentials** directly, which is the simplest path since they are already in your terminal. If you prefer a **Bedrock bearer token** instead (for example to match the App setup), export it before launching Codex:

```bash
export AWS_BEARER_TOKEN_BEDROCK=$(python3 -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='us-east-2'))")
```

Codex uses the bearer token when present and otherwise falls back to your AWS profile.
:::

## 2. Config anatomy

The configuration file is the control plane for Codex behavior. For this workshop, focus on the settings that shape model choice, approvals, sandboxing, and task speed:

| Setting | What it controls | Workshop guidance |
|---------|------------------|-------------------|
| `model` | Default model for Codex sessions | `openai.gpt-5.4` (the `openai.` prefix is required on Bedrock) |
| `model_provider` | Which provider Codex sends requests to | `amazon-bedrock`, the built-in Bedrock provider |
| `web_search` | The built-in hosted web-search tool | `disabled`. Bedrock rejects hosted tools |
| `approval_policy` | When Codex pauses for permission | `on-request` for interactive workshops |
| `sandbox_mode` | What Codex can read/write by default | `workspace-write` for local coding tasks |
| `model_reasoning_effort` | How much reasoning to spend | Lower for quick tasks, higher for design or review |

User-level configuration lives in `~/.codex/config.toml`. Project-specific settings can live in `.codex/config.toml` after the project is trusted, but machine-local provider, auth, and telemetry settings should stay in user-level config.

(Optional) Create profiles for different reasoning budgets so you can switch task modes with a flag:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
cat >> ~/.codex/config.toml << 'EOF'

[profiles.fast]
model_reasoning_effort = "low"

[profiles.deep]
model_reasoning_effort = "high"
EOF
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
@"

[profiles.fast]
model_reasoning_effort = "low"

[profiles.deep]
model_reasoning_effort = "high"
"@ | Add-Content "$env:USERPROFILE\.codex\config.toml"
:::
::::
:::::

Select a profile with the `--profile` flag:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex --profile fast
codex --profile deep
:::

## 3. Verify the configuration

1. Start Codex from the workshop project:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
codex
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
cd "$env:USERPROFILE\workshop\sample-openai-on-aws\bedrock-chat"
codex
:::
::::
:::::

2. Run the status command to confirm Codex is using the Bedrock provider and the workshop model:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/status
:::

You should see output similar to:

```
Model: openai.gpt-5.4
Provider: amazon-bedrock
Approval Policy: on-request
Sandbox Mode: workspace-write
```

3. Ask Codex a quick question to confirm the round trip to Bedrock works:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
In one sentence, what does this repository do?
:::

A normal answer means Codex is talking to GPT on Bedrock.

:::alert{type="warning" header="If a bearer token expires mid-session"}
If you authenticated with `AWS_BEARER_TOKEN_BEDROCK`, it lasts about 12 hours. On a `401`, exit Codex, re-export a fresh token, and relaunch from the same terminal. The AWS-profile path refreshes automatically and does not have this issue.
:::

## 4. Switching models

The `model = "openai.gpt-5.4"` line sets the default. To try GPT-5.5, change it to `openai.gpt-5.5` and restart Codex, or switch live in a session with `/model`. The `openai.` prefix is required either way on Bedrock.

## 5. Team deployment with config files

For production team deployments, Codex supports a configuration hierarchy that provides layered settings:

- **User config** (`~/.codex/config.toml`) — Personal settings that apply across all your projects. This is what you configured above.
- **Project config** (`.codex/config.toml` in the repository) — Project-specific settings that are version-controlled and shared with the team. Use this for safe project defaults such as approvals and sandboxing.
- **System config** (`/etc/codex/config.toml`) — Organization-wide settings deployed by IT or DevOps.

**Settings precedence** (highest to lowest): CLI flags, then profile, project, user, system, and finally built-in defaults.

:::alert{type="warning" header="Keep machine-local settings out of project config"}
Do not commit Bedrock credentials, bearer tokens, telemetry routing, or user-specific profile selection into `.codex/config.toml`. Keep those in `~/.codex/config.toml` or managed configuration.
:::

## 6. Congratulations!

You've configured the Codex CLI to run against GPT on Amazon Bedrock using the credentials from Getting Started, and learned how to use profiles to tune reasoning effort per task.
