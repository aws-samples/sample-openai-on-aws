---
title: "Enable vim mode for power users"
weight: 34
---

Enable vim keybindings in the Codex composer for efficient text editing.

:::alert{type="info" header="Feature availability"}
Vim mode availability and configuration may vary by Codex version. Check `/help` or your configuration options for TUI settings.
:::

## 1. Toggle vim mode

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/vim
:::

## 2. Available vim features

With vim mode enabled:

- **Modal editing**: Normal, insert, visual modes
- **Motions**: hjkl, w, b, e, 0, $
- **Commands**: dd, yy, p, u (undo)
- **Search**: /, n, N

## 3. Persist vim mode

Add to your :code[~/.codex/config.toml]{showCopyAction=false}:

:::code{showCopyAction="true" language="toml"}
[tui]
vim_mode = true
:::

## 4. Customize keymaps

View and modify keybindings:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/keymap
:::

## 5. Congratulations!

You've enabled vim mode for efficient text editing in Codex.
