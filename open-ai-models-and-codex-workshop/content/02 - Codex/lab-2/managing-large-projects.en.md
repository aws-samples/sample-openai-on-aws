---
title: "Manage large projects with session management and subagents"
weight: 26
---

Large projects require efficient context management and the ability to parallelize work. Codex provides session management and subagents to handle complex, multi-file tasks. The Codex App is especially helpful here because it gives you a visual way to monitor multiple threads, inspect diffs, and keep the main task moving.

:::alert{type="warning" header="Command syntax"}
The commands shown here (`codex resume`, `/fork`, `/compact`, `/agent`) demonstrate concepts that may have different syntax in your Codex version. Use `codex --help` and `/help` to see available commands.
:::

## 1. Session management

### Resume previous sessions

Pick up where you left off without repeating context:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex resume --last
:::

Or list available sessions:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex resume
:::

Sessions preserve:
- Full conversation transcript
- Plan history
- Approval decisions
- Current goal

### Fork conversations

Explore alternatives without losing your original work:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/fork
:::

This creates a branch of your current conversation. Make experimental changes, and if they don't work out, you still have the original.

### Compact context

When conversations get long, summarize earlier turns:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/compact
:::

This preserves essential context while freeing up the context window for new work.

## 2. Subagents

For large tasks, spawn multiple agents that work concurrently.

![Subagents let Codex parallelize investigations and report back](/static/images/codex/onboarding-deck/slide-41.png)

![Subagents vs Agent Teams](/static/images/codex/lab-2/subagents-vs-agent-teams.png)

### How subagents work

Subagent workflows are most useful when you explicitly ask Codex to split a task into independent lines of investigation. Codex orchestrates the workers, waits for the requested results, and returns a consolidated response:

```
Main Session: "Refactor this codebase to use dependency injection"
    │
    ├── Subagent 1: Analyze current dependencies
    ├── Subagent 2: Update module A
    └── Subagent 3: Update module B
    │
    └── Merged results
```

Try a review prompt that naturally parallelizes:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Review the current branch against the base branch. Spawn one agent per review area, wait for all results, and summarize the findings:
1. Security risks
2. Code quality
3. Bugs and edge cases
4. Test flakiness
5. Maintainability
:::

:::alert{type="info" header="Explicit delegation"}
Codex only spawns subagents when you ask it to. Use them for independent workstreams; keep simple sequential work in the main session.
:::

### View subagent work

Switch to view a subagent's thread:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/agent
:::

### Monitor background work

List background terminals and their status:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/ps
:::

Stop all background work:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/stop
:::

:::alert{type="warning" header="Token usage"}
Subagents consume more tokens than single-agent runs. Use them strategically for tasks that genuinely benefit from parallelization.
:::

:::alert{type="info" header="Approvals and sandboxing"}
Subagents inherit the current sandbox and approval settings. In interactive sessions, approval requests can surface from inactive subagent threads, so review the source thread label before approving.
:::

## 3. Custom agents

For repeatable work, define named custom agents with their own instructions. Personal agents live under `~/.codex/agents/`; project-scoped agents live under `.codex/agents/`.

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p .codex/agents
cat > .codex/agents/test-reviewer.toml << 'EOF'
name = "test-reviewer"
description = "Review changes for test coverage gaps and flaky behavior"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
You are a test-focused reviewer.
Look for missing regression tests, flaky timing assumptions, weak assertions,
and test fixtures that do not match production behavior.
Return prioritized findings with file paths and suggested tests.
"""
EOF
:::

Then ask Codex to use it:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Spawn the test-reviewer custom agent to review my current diff. Wait for the result, then summarize the highest-priority test gaps.
:::

## 4. Context window management

For large codebases, manage what context Codex has:

### Focus on specific files

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/mention src/api/routes.py src/models/user.py
:::

### Use the @ shortcut

In the composer, type :code[@]{showCopyAction=false} for fuzzy file search.

### Incremental development

Break large tasks into smaller steps:

1. Design the interface
2. Implement core logic
3. Add edge cases
4. Write tests

This approach keeps context focused and produces better results.

## 5. Congratulations!

You've learned how to manage large projects with session management, subagents, and context optimization. You can now tackle complex, multi-file tasks efficiently.
