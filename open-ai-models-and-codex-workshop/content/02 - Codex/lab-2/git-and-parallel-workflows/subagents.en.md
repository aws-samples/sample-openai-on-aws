---
title: "(Optional) Orchestrate parallel work with subagents"
weight: 3
---

Take parallel development to the next level by using Codex's subagent capabilities to coordinate multiple tasks working together on complex projects.

:::alert{type="info" header="App and CLI visibility"}
Subagent workflows are designed for the Codex App and CLI. Use `/help` in your Codex version to confirm the available inspection and navigation commands.
:::

## 1. Understand subagents

Codex can spawn subagents to handle specific tasks independently. Subagents work in isolated context windows and report results back to the main agent, enabling parallel task execution.

![Subagents let Codex parallelize investigations and report back](/static/images/codex/onboarding-deck/slide-41.png)

## 2. When to use subagents

Subagents are useful when:

- **Research tasks**: Investigating multiple files or documentation sources simultaneously
- **Code analysis**: Reviewing different parts of the codebase in parallel
- **Testing strategies**: Exploring multiple implementation approaches
- **Large refactors**: Handling different subsystems independently

## 3. Spawn subagents for parallel research

1. Navigate to your project directory:

:::code{showCopyAction="true" language="bash"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

2. Start Codex:

:::code{showCopyAction="true" language="bash"}
codex
:::

3. Ask Codex explicitly to use subagents for parallel investigation:

:::code{showCopyAction="true" language="text"}
I want to add multi-user conversation rooms to this chat app. Use subagents to research:
- One subagent to analyze the current chat session state management
- One subagent to investigate WebSocket options for real-time message sync
- One subagent to research the conversation bookmarks system for shared sessions
Then synthesize the findings into an implementation plan.
:::

Codex spawns multiple subagents that work independently, waits for the requested results, and reports the synthesized findings back in the main thread.

## 4. Run a parallel code review

Use subagents to review different aspects of your code simultaneously:

:::code{showCopyAction="true" language="text"}
Create subagents to review our recent changes:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Wait for all three to complete, then summarize the findings by severity.
:::

Each reviewer works from the same code but applies a different filter. The main agent synthesizes findings across all three after they finish.

## 5. Investigate with competing hypotheses

When the root cause of a bug is unclear, have subagents test different theories in parallel:

:::code{showCopyAction="true" language="text"}
Users report the chat interface freezes during streaming responses. Spawn subagents to investigate different hypotheses:
- One checking for memory leaks in message rendering
- One analyzing state management race conditions in the SSE handler
- One reviewing event handler performance in the chat input
Report which hypothesis is most likely.
:::

## 6. Subagent best practices

| Guideline | Description |
|-----------|-------------|
| Clear task scope | Give each subagent a specific, well-defined task |
| Independent work | Ensure subagent tasks don't overlap or conflict |
| Result synthesis | Plan how to combine subagent findings |
| Resource awareness | Consider token usage when spawning multiple subagents |

:::alert{type="info" header="Token usage"}
Subagents consume additional tokens since each maintains its own context. Use them when parallel exploration adds genuine value rather than for simple sequential tasks.
:::

:::alert{type="info" header="Approvals and sandboxing"}
Subagents inherit your current sandbox and approval settings. If an inactive subagent requests approval, check the source thread before approving the action.
:::

## 7. Compare with sequential approaches

| Approach | Best For | Token Cost |
|----------|----------|------------|
| Sequential | Simple, dependent tasks | Lower |
| Subagents | Independent, parallelizable tasks | Higher |
| Worktrees + sessions | Long-running parallel features | Highest |

Use subagents for quick, focused workers that report back. Use git worktrees with separate Codex sessions when tasks require sustained, independent development.

## 8. Congratulations!

You've learned how to orchestrate parallel work using Codex's subagent capabilities. This enables you to coordinate parallel exploration, code review, debugging, and feature research across multiple independent contexts that report back to your main session.
