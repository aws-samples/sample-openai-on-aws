---
title: "Ask side questions with conversation branching"
weight: 31
---

Side conversations let you explore tangents without polluting your main conversation history.

:::alert{type="info" header="Command availability"}
Conversation branching features may have different command names in your Codex version. Use `/help` to see available commands like side conversations, forking, or branching.
:::

## 1. Side conversations

Launch an ephemeral side conversation:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/side
:::

In the side conversation, ask quick questions:

```
What's the syntax for Python decorators again?
```

When you close the side conversation, you return to your main session with its context intact.

## 2. Fork conversations with /fork

Create a persistent branch of your conversation:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/fork
:::

Unlike :code[/side]{showCopyAction=false}, forked conversations are saved and can be resumed later with :code[codex resume]{showCopyAction=false}.

## 3. When to use each

| Command | Persistence | Use Case |
|:--------|:------------|:---------|
| :code[/side]{showCopyAction=false} | Temporary | Quick questions, syntax lookups |
| :code[/fork]{showCopyAction=false} | Permanent | Exploring alternative approaches |

## 4. Congratulations!

You can now use side conversations to stay focused while exploring tangents.
