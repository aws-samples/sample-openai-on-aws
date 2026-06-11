---
title: "Create a team Codex operating model"
weight: 41
---

Before scaling Codex across a team, decide which behaviors belong in the repository, which belong in user configuration, and which require central governance.

This exercise creates a lightweight operating model that you can adapt for your own team.

## 1. What to standardize

| Artifact | Recommended location | Purpose |
|----------|----------------------|---------|
| `AGENTS.md` | Repository root | Coding standards, repo map, test commands, review expectations |
| `.codex/config.toml` | Repository `.codex/` folder | Safe project defaults such as sandboxing and approval posture |
| `.codex/agents/*.toml` | Repository `.codex/agents/` folder | Shared custom agents for review, testing, security, or docs |
| `.codex/rules/*.rules` | Repository or user config layer | Command approval rules for safe automation |
| `~/.codex/config.toml` | User home folder | Machine-local provider, auth, profile, notification, and telemetry settings |

## 2. Create project-local defaults

From the workshop project folder, create a minimal project configuration:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
mkdir -p .codex/agents .codex/rules
${EDITOR:-nano} .codex/config.toml
:::

Add safe defaults for a shared repository:

:::code{showCopyAction="true" language="toml" copyAutoReturn="true"}
approval_policy = "on-request"
sandbox_mode = "workspace-write"
model_reasoning_effort = "medium"
:::

Do not put provider credentials, `OPENAI_API_KEY`, telemetry destinations, or personal profile selection in project config.

## 3. Add a reusable review agent

Create a custom agent that the team can use during PR preparation:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat > .codex/agents/pr-reviewer.toml << 'EOF'
name = "pr-reviewer"
description = "Review a branch for bugs, missing tests, and maintainability risks"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
Review the current diff as a senior engineer.
Prioritize bugs, behavioral regressions, missing tests, and maintainability risks.
Return findings first, ordered by severity, with file paths.
If there are no findings, say so clearly and mention residual test gaps.
"""
EOF
:::

## 4. Add command approval rules

Create a project-level rules file for this repository:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat > .codex/rules/workshop.rules << 'EOF'
prefix_rule(
    pattern = ["git", ["status", "diff", "log"]],
    decision = "allow",
    justification = "Read-only git inspection is safe in this project"
)

prefix_rule(
    pattern = ["git", "push"],
    decision = "prompt",
    justification = "Developers should review before publishing changes"
)
EOF
:::

Restart Codex after editing rules so they are loaded.

## 5. Ask Codex to review the operating model

In the Codex App or CLI, ask:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Review this repository's Codex operating model. Inspect AGENTS.md, .codex/config.toml, .codex/agents, and .codex/rules. Tell me what should be committed, what should remain user-local, and what requires security review before team rollout.
:::

## 6. Congratulations!

You now have a compact pattern for rolling Codex out to a team: shared instructions, safe project defaults, reusable custom agents, and explicit command approval rules.
