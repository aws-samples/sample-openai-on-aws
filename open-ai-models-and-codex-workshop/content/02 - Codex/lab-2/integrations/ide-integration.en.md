---
title: "(Optional) Integrate Codex with your IDE"
weight: 2
---

Codex can be integrated with popular IDEs to provide a seamless AI-assisted development experience directly within your editor.

## 1. VS Code integration

While Codex is primarily a CLI tool, you can enhance your VS Code workflow by integrating terminal-based Codex sessions with your editing experience.

### Use VS Code integrated terminal

1. Open your project directory in VS Code or your preferred IDE. From a terminal, first navigate to the project:

:::code{showCopyAction="true" language="bash"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

If you use VS Code and have the `code` shell command installed, you can then run `code .`.

2. Open the integrated terminal (:code[Ctrl+`]{showCopyAction=false} or :code[Cmd+`]{showCopyAction=false} on macOS).

3. Start Codex in the terminal:

:::code{showCopyAction="true" language="bash"}
codex
:::

Now you can interact with Codex while seeing your code changes reflected immediately in the editor.

### Split terminal workflow

For an optimal workflow, split your terminal:

1. Open a split terminal in VS Code (:code[Ctrl+Shift+5]{showCopyAction=false})
2. Run Codex in one pane for AI assistance
3. Use the other pane for git, testing, or other commands

This allows you to:
- See Codex suggestions alongside your code
- Test changes immediately in a separate terminal
- Keep context while switching between tasks

## 2. Terminal multiplexer workflow

For power users, combine Codex with tmux or screen for advanced session management:

### Using tmux

1. Create a new tmux session:

:::code{showCopyAction="true" language="bash"}
tmux new-session -s codex-dev
:::

2. Split the window horizontally:

:::code{showCopyAction="true" language="bash"}
tmux split-window -h
:::

3. Run Codex in one pane and your editor in another.

### Session persistence

With tmux, your Codex session persists even if you disconnect:

:::code{showCopyAction="true" language="bash"}
# Detach from session
tmux detach

# Reattach later
tmux attach -t codex-dev
:::

## 3. Keyboard shortcuts reference

| Action | Shortcut |
|--------|----------|
| Accept suggestion | Enter |
| Cancel current operation | Ctrl+C |
| Clear screen | Ctrl+L |
| Exit Codex | Ctrl+D or type "exit" |
| Undo last change | Check `/help` for undo commands |

## 4. Best practices for IDE integration

| Practice | Description |
|----------|-------------|
| Keep editor visible | Position your terminal so you can see code changes in real-time |
| Use auto-save | Enable auto-save in your editor to see Codex changes immediately |
| Split workflow | Use separate terminals for Codex and other commands |
| Session management | Use tmux for long-running development sessions |

:::alert{type="info" header="Current IDE options"}
Codex IDE extension support is available for supported editors, and the exact editor list can change over time. Check the [OpenAI documentation](https://developers.openai.com/codex/) for the latest integration options.
:::

## 5. Congratulations!

You've learned how to integrate Codex into your IDE workflow for a seamless AI-assisted development experience. Whether using VS Code's integrated terminal, split panes, or terminal multiplexers like tmux, you can now work efficiently with Codex alongside your favorite editing tools.
