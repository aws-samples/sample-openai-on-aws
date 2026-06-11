---
title: "Part 2: 💻 OpenAI Codex App, IDE, and CLI"
weight: 20
---

![Codex surfaces across App, IDE, and CLI](/static/images/codex/onboarding-deck/slide-04.png)

### Supercharge your team development with OpenAI Codex

In this hands-on workshop, you will learn how to accelerate team development with OpenAI Codex across the **Codex App**, **IDE extensions**, and **CLI**, all running GPT models on Amazon Bedrock. The App gives you a visual surface for chat, diffs, workspaces, skills, worktrees, automations, and parallel work. The IDE and CLI cover editor-native and terminal-native workflows. Lab 1 sets up all three, and the exercises call out where each surface fits best.

:::alert{type="info" header="Credentials carry over from Getting Started"}
Codex connects to GPT on Bedrock through its built-in `amazon-bedrock` provider, using the AWS credentials and region you set up in Getting Started. There is no separate OpenAI account or API key for the Bedrock path. Lab 1 shows the exact config for each surface.
:::

:::alert{type="info" header="Workshop project"}
Before the hands-on development exercises, clone the `codex-advanced-patterns` branch of `aws-samples/sample-openai-on-aws` and work from `sample-openai-on-aws/bedrock-chat`. Lab 1 includes the exact clone command.
:::

## 1. Choose your Codex surface

| Surface | Use it when you want... | Workshop role |
|:--------|:------------------------|:--------------|
| **Codex App** | A visual chat surface, richer diffs, multiple workspaces, skills, worktrees, automations, and tasks beyond code | Set up first in Lab 1 |
| **IDE extension** | Incremental help while staying inside VS Code, Cursor, Windsurf, JetBrains, or Xcode | Good for editor-first attendees |
| **CLI** | Terminal-native workflows, slash commands, scripting, and fast repo tasks | Set up alongside the App |

**Suitable for:** This workshop is designed for developers, engineering leaders, technical leads, and DevOps professionals from small to large teams looking to learn Codex CLI concepts to improve productivity and scale and/or roll out Codex to their team.

**Level:** 300 (Advanced). No background knowledge necessary, however familiarity with Python or JavaScript and AWS services will be useful.

**Duration:** We expect the workshop to take approximately **3 hours** to complete.

:::alert{type="warning" header="This workshop is currently only supported for AWS-run events"}
This workshop is optimized for AWS-run events only. If you would like to run this in your own AWS account, ensure to clean up any unused resources to avoid incurring costs.
:::
