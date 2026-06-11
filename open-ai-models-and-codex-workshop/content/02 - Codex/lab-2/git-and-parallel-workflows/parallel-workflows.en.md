---
title: "(Optional) Use git worktrees for parallel workflows"
weight: 1
---

Git worktrees allow you to have multiple working directories from the same repository, each checked out to a different branch. This lets you work on multiple features simultaneously without switching branches or stashing changes.

## 1. Create a new worktree

1. Navigate to your project directory:

:::code{showCopyAction="true" language="bash"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

2. Create a worktree for the message history export feature:

:::code{showCopyAction="true" language="bash"}
git worktree add ../chat-history-export -b feature/history-export
:::

This creates a new directory at `../chat-history-export` with its own working tree, checked out to the `feature/history-export` branch. Your main directory stays on its current branch.

## 2. Work on a feature in your main directory

3. In your current terminal (still in `bedrock-chat`), start Codex to work on the conversation clear button:

:::code{showCopyAction="true" language="bash"}
codex
:::

:::code{showCopyAction="true" language="text"}
Add a conversation clear button that resets the chat history
:::

## 3. Work on another feature in the worktree

4. Open a new terminal window and navigate to the worktree:

:::code{showCopyAction="true" language="bash"}
cd ../chat-history-export
:::

5. Start Codex in this worktree:

:::code{showCopyAction="true" language="bash"}
codex
:::

:::code{showCopyAction="true" language="text"}
Add a message history export feature that lets users download their chat as JSON
:::

Both Codex sessions now work independently on different features without interfering with each other's changes.

## 4. Manage your worktrees

6. List all active worktrees:

:::code{showCopyAction="true" language="bash"}
git worktree list
:::

This shows all worktrees and their current branches.

## 5. Merge and clean up

7. When your history export feature is complete, merge it and remove the worktree:

:::code{showCopyAction="true" language="bash"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
git checkout codex-advanced-patterns
git merge feature/history-export
git worktree remove ../chat-history-export
:::

:::alert{type="info" header="When to use worktrees"}
Use worktrees when:
- Working on multiple features that would conflict if developed in the same branch
- Comparing different implementation approaches side-by-side
- Needing to quickly switch context without stashing changes

For quick experimentation on a single feature, use undo/rewind features (check `/help` for available commands) instead.
:::

## 6. Congratulations!

You've learned to use git worktrees for parallel development with Codex. This enables you to work on multiple features simultaneously without branch switching, making context switching more efficient for complex projects.
