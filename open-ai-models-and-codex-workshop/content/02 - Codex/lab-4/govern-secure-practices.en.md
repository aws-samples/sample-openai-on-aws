---
title: "(Optional) Govern and establish secure practices"
weight: 47
---

In addition to the observability and cost controls covered in this lab, this page covers practical tips for team governance and security — from embedding security rules in your codebase to governing tool access as your team grows.

:::alert{type=success header="Reference guide"}
This page is informational. No hands-on steps are required. Use it as a reference when planning your own organization-wide deployment.
:::

## 1. Security by design

A secure-by-design approach treats Codex's configuration as code — committing policies to source control, building approved pattern libraries, and using automation to reinforce standards alongside individual developer judgement.

**`AGENTS.md` as a security policy file.** Commit security rules directly to your repository alongside the code they govern. When Codex opens a project, it automatically loads the repository-level `AGENTS.md`, making your security guidance available as context for every session:

:::code{showCopyAction="true" language="markdown"}
## Security

- Never log PII. Redact before logging.
- IAM roles only — no long-lived access keys in code.
- Validate all external input at system boundaries.
- SQL queries must use parameterized statements.
- Secrets go in AWS Secrets Manager, not environment variables.
:::

For organization-wide rules that apply across every repository, distribute an `AGENTS.md` via `~/.codex/AGENTS.md`.

## 2. Treat agent configurations as supply chain artifacts

`.codex/` settings, `AGENTS.md` files, skill definitions, and MCP configuration files are part of your execution surface — not just developer tooling. Treat changes to these files with the same scrutiny as changes to CI/CD pipelines or deployment configuration.

Practical controls:

- **Version-control your configuration** — Commit your settings, `AGENTS.md` content, and skill files to a shared internal repository. Treat configuration changes with the same review process as code changes.
- **Require code review for config changes** — Add `.codex/`, `AGENTS.md`, and `*.mcp.json` to your branch protection rules or CODEOWNERS file so changes go through review before merging.
- **Scan configs in CI** — Add a CI check that lints skill files and `AGENTS.md` for unusual instructions, permission escalations, or unexpected network references before they land on the default branch.
- **Use short-lived, scoped credentials** — Do not give Codex agent workflows your personal accounts or org-wide tokens. Create dedicated bot identities with the minimum permissions the task requires, and rotate credentials after untrusted runs.

## 3. Code review as a security layer

Codex can assist with security-focused code reviews, complementing static analysis tools with context that requires understanding the broader codebase.

**Layered review approach:**

- **Static analysis layer** — Surface known vulnerability patterns (injection, XSS, insecure deserialization) and flag insecure dependencies.
- **Architectural layer** — Review trust boundaries, data flows between components, and authentication/authorization design.
- **Compliance layer** — Check against your organization's specific requirements (SOC 2, HIPAA, PCI-DSS) and internal security standards.

## 4. Govern command approvals with rules

Rules let teams control which commands Codex can run outside the sandbox. Use them to pre-approve low-risk commands, prompt for sensitive commands, and block commands that should never run automatically.

![Rules help teams control which commands Codex can run automatically, with permission, or never](/static/images/codex/onboarding-deck/slide-38.png)

:::alert{type="info" header="Rules are startup-loaded"}
Codex scans `.rules` files from active config layers when it starts. Restart Codex after editing rules. Project-local rules under `.codex/rules/` load only after the project config layer is trusted.
:::

Create a user-level rules file:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/.codex/rules
${EDITOR:-nano} ~/.codex/rules/default.rules
:::

Add rules that match your team's risk posture:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
# Allow low-risk local inspection commands.
prefix_rule(
    pattern = ["git", ["status", "diff", "log"]],
    decision = "allow",
    justification = "Read-only git inspection is safe for workshop tasks",
    match = [
        "git status",
        "git diff",
        "git log --oneline -5",
    ],
)

prefix_rule(
    pattern = ["rg"],
    decision = "allow",
    justification = "Ripgrep is used for read-only source search",
    match = [
        "rg OpenAI content",
        "rg --files",
    ],
)

# Prompt before commands that may publish, mutate remote state, or read remote systems.
prefix_rule(
    pattern = ["git", "push"],
    decision = "prompt",
    justification = "Pushing changes should be reviewed by the developer",
    match = [
        "git push origin mainline",
    ],
)

prefix_rule(
    pattern = ["gh", "pr", "view"],
    decision = "prompt",
    justification = "Reading PR metadata is allowed with approval",
    match = [
        "gh pr view 123",
        "gh pr view --repo openai/codex",
    ],
    not_match = [
        "gh pr --repo openai/codex view 123",
    ],
)

# Block destructive shortcuts. Prefer explicit, reviewed cleanup steps.
prefix_rule(
    pattern = ["rm", "-rf"],
    decision = "forbidden",
    justification = "Use a reviewed cleanup command for destructive file deletion",
    match = [
        "rm -rf build",
    ],
)
:::

Rules use exact command-prefix matching. If more than one rule matches, Codex applies the most restrictive decision: `forbidden` beats `prompt`, and `prompt` beats `allow`.

:::alert{type="warning" header="Shell wrappers"}
Treat shell wrappers carefully. Codex can split simple command chains like `git status && rg TODO`, but advanced shell features such as variable expansion, wildcards, and complex substitutions are evaluated conservatively. Keep allowed rules narrow and obvious.
:::

## 5. Govern MCP server approvals

MCP servers extend Codex with additional tools — database access, internal APIs, deployment triggers. Before approving an MCP server for team use, evaluate:

- **Tool surface area** — What actions can the server take? Read-only is lower risk than read/write.
- **Data exfiltration risk** — Does the server make outbound network calls? To where?
- **Authentication** — Does the server require credentials? How are they stored?
- **Scope** — Is the server scoped to specific resources, or does it have broad access?

**Recommended process for new MCP server requests:**

1. Developer submits a request with the server name, repository link, and intended use case.
2. Security team reviews: inspect the source code or vendor trust assessment, run the server in a sandbox, and check outbound network destinations.
3. If approved, add to the approved MCP servers list and publish the updated configuration.
4. Run quarterly audits to review the installed tool list and remove servers that are no longer in active use.

:::alert{type=warning header="Community MCP servers"}
Treat community MCP servers with the same scrutiny as any third-party dependency. A server with write access to your filesystem or the ability to make arbitrary HTTP requests carries meaningful risk. Prefer vendors with published security assessments, or build internal servers for sensitive operations.
:::

## 6. Learn more

- [OpenAI Codex documentation](https://platform.openai.com/docs/codex)
- [Amazon Bedrock security best practices](https://docs.aws.amazon.com/bedrock/latest/userguide/security.html)

## 7. Congratulations!

You have completed Lab 4. You now have the tools to monitor Codex usage with dashboards, manage costs with quota policies, and govern your organization's deployment with security practices, MCP approval workflows, and embedded security policies.
