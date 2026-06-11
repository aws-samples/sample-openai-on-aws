---
title : "Lab 3: Implement and distribute advanced workflows"
weight : 30
---

Now that you understand key Codex concepts like team standards, extensibility, and workflows, let's explore some common patterns that can be packaged and distributed across your team. These reusable workflows enable standardized security reviews, automated documentation, quality gates, and development loops that any team member can leverage.

:::alert{type="info" header="Prerequisites"}
Ensure you have completed Lab 1 and have Codex configured to run GPT on Amazon Bedrock before proceeding with these advanced patterns.
:::

## 1. What you'll learn

In this lab, you will:

- Distribute these workflows as reusable patterns for team-wide adoption
- Implement security review workflows that can be shared across projects
- Generate smart documentation using packaged slash commands
- Set up quality gates through hook configurations
- Explore the extensibility mechanisms available in Codex

![The engineer's role shifts toward setting agents up for success](/static/images/codex/onboarding-deck/slide-29.png)

## 2. Codex extensibility overview

Codex provides multiple extensibility mechanisms to customize your development workflow:

| Mechanism | Purpose | Scope | Distribution |
|-----------|---------|-------|--------------|
| **AGENTS.md** | Team standards, coding conventions, project structure | Project or global | Git repository |
| **Custom commands** | Simple reusable prompts with :code[/command-name]{showCopyAction=false} | Project or global | Git repository |
| **Skills** | Advanced prompts with metadata and supporting files | Project or global | Git repository |
| **Custom agents** | Specialized subagents with their own instructions and optional model settings | Project or global | Git repository |
| **MCP servers** | External tool integration via Model Context Protocol | Installed per environment | npm, or custom installation |
| **Hooks** | Automated actions triggered at workflow events | Project or global | Git repository |

## 3. Explore example patterns

Run the following commands in your **terminal** (not inside Codex).

1. Navigate to the workshop directory and create folders for your agents and commands:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/.codex/agents ~/.codex/commands ~/.codex/hooks
:::

2. Create a sample security reviewer custom agent:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat > ~/.codex/agents/security-reviewer.toml << 'EOF'
name = "security-reviewer"
description = "Perform OWASP vulnerability assessment of the codebase"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
You are a security expert performing a comprehensive security review.

Review process:
- Check all user inputs for proper sanitization.
- Review authentication mechanisms for weaknesses.
- Verify authorization and access-control implementations.
- Check encryption and secure data handling.
- Look for SQL, XSS, and command injection vulnerabilities.
- Check dependencies for known vulnerability patterns.

Output format:
- Severity: Critical/High/Medium/Low
- Location: File and line number
- Description: What the issue is
- Recommendation: How to fix it
"""
EOF
:::

Custom agents are standalone TOML files. Use `~/.codex/agents/` for personal agents and `.codex/agents/` for project-scoped agents that should travel with the repository.

3. Ask Codex to use the agent:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Spawn the security-reviewer custom agent to review the current repository for authentication, authorization, injection, and secret-handling risks. Wait for the agent result and summarize the top findings.
:::

## 4. Get started

Ready to implement advanced workflows? Continue to the next section to learn how to use these patterns for security reviews, documentation generation, and quality gates.
