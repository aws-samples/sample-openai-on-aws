---
title: "(Optional) Interact with git to understand project history and context"
weight: 2
---

Now that you're working from the `codex-advanced-patterns` branch of the sample repository, let's learn how Codex handles git operations. Codex can analyze the project's existing evolution, generate contextual commit messages, and manage complex git workflows, all while understanding the work you've already done.

## 1. Working with your git repository

Because you cloned `sample-openai-on-aws`, your project already has git history and a remote configured. Before asking Codex to commit or branch, confirm that you're in the right folder and on the workshop branch.

1. Ensure you're in the cloned Bedrock Chat project directory:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

2. Confirm the active branch and repository status:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
git branch --show-current
git status
:::

You should see `codex-advanced-patterns` as the active branch.

3. Check the recent git history:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
git log --oneline -5
:::

You should see recent commits from the sample repository. This gives Codex useful context about how the project has evolved.

## 2. Project understanding from git history

Let's make an enhancement to the chat app, have Codex commit it, and then analyze your git history to understand the project evolution.

1. Start Codex:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex
:::

2. Make a small improvement to the chat interface styling:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Add a subtle animation to new messages as they appear in the chat. Commit to git when done.
:::

3. Ask Codex to analyze and commit:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Look at git history and summarize it for me.
:::

Codex examines your git history and provides a summary of the commits and changes.

## 3. Codex writes better commit messages than most humans

Codex follows commit message conventions naturally:

| Element | Example |
|---------|---------|
| Type prefix | `feat:`, `fix:`, `docs:`, `style:`, `refactor:` |
| Summary line | Short, descriptive, present tense |
| Body | Detailed explanation when warranted |

Here's what Codex might produce for chat interface work:

```
feat: Add typing indicator animation to chat interface

- Implemented CSS animation for streaming response indicator
- Dots pulse while waiting for the model response
- Animation runs continuously until response completes
```

That's a commit message you'd be proud to have in your history, and you didn't have to write it.

## 4. Other git tasks Codex handles

| What You Need | What to Say |
|---------------|-------------|
| Commit changes | "Commit these changes with a good message" |
| Check status | "What files have changed?" |
| View diff | "Show me what changed in the chat component file" |
| Create branch | "Create a new branch called feature/dark-mode" |
| View history | "Show me recent commits" |
| Compare branches | "What's different between this branch and codex-advanced-patterns?" |

:::alert{type="warning" header="Git safety"}
Codex is cautious about destructive git operations. Unless you explicitly request them, it won't force push, hard reset, interactive rebase, or delete branches with unmerged changes. The dangerous stuff requires deliberate intent.
:::

## 5. Feature branches and pull requests

Now that you've seen how Codex works with git history and commits, let's explore feature branch workflows and pull request creation.

1. Create a feature branch for a new enhancement:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
git checkout -b feature/chat-dark-mode
:::

2. In Codex, add a new feature (dark mode theme toggle for the chat interface):

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Add a dark mode theme toggle button that switches between light and dark mode for the chat interface. Update the styling to support both themes.
:::

3. Have Codex create a pull request:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Create a pull request for my dark mode feature. Generate an appropriate title and description based on the changes to the Bedrock Chat App.
:::

You should see a generated pull request using the GitHub CLI if your environment is authenticated and you have permission to push to the repository.

:::alert{type=info header="Repository permissions"}
The cloned sample repository includes a remote, but workshop participants may not have permission to push directly to it. Codex can still analyze your Bedrock Chat changes and generate the PR title and description locally. Push only if you have access to your own fork or the shared workshop repository.
:::

## 6. Hands-on practice

Try these git scenarios with Codex:

1. **Commit message generation**: Make several small changes and have Codex create commit messages
2. **History investigation**: Ask Codex to find when specific features were added
3. **Conflict resolution**: Create a merge conflict and have Codex help resolve it

## 7. Congratulations!

You've learned to use Codex for comprehensive git operations with real repository history. This will streamline your version control workflow and improve commit quality through intelligent analysis of your project's evolution.
