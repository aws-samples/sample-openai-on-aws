---
title: "Conversation State"
weight: 3
---

The Responses API can support both stateful and manually managed conversation patterns. This matters because production applications need to choose how much state lives with the API and how much state their own application stores.

Use this rule of thumb:

| Pattern | How it works | When to use it |
|---------|--------------|----------------|
| `previous_response_id` | Store a response and pass its ID into the next request | Simple multi-turn apps, prototypes, agent loops |
| Manual history | Keep the messages in your app and pass the relevant history each turn | Strict retention control, custom summarization, app-owned transcripts |
| Conversations | Store a longer-lived conversation object | Apps that need durable threads across sessions or devices |

:::alert{type="info" header="State is a design choice"}
The model still receives context on each turn. The difference is whether you pass that context manually, reference a previous response, or attach the response to a Conversation. Even when using stateful patterns, keep an eye on context-window size and token cost.
:::

## 1. Try `previous_response_id`

Copy the below code to a file `state_previous_response.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

first = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="In one sentence, explain what DynamoDB is.",
    store=True,
)
print("Turn 1:", first.output_text)

second = client.responses.create(
    model=os.environ["MODEL_ID"],
    previous_response_id=first.id,
    input="Now give one practical ecommerce use case for it.",
    store=True,
)
print("Turn 2:", second.output_text)
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 state_previous_response.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python state_previous_response.py
:::
::::
:::::

The second request does not resend the first answer. Instead, it references the stored response by ID.

## 2. Try manual history

Copy the below code to a file `state_manual_history.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

history = [
    {"role": "user", "content": "In one sentence, explain what DynamoDB is."}
]

first = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=history,
    store=False,
)
print("Turn 1:", first.output_text)

history.append({"role": "assistant", "content": first.output_text})
history.append({"role": "user", "content": "Now give one practical ecommerce use case for it."})

second = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=history,
    store=False,
)
print("Turn 2:", second.output_text)
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 state_manual_history.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python state_manual_history.py
:::
::::
:::::

Here your application owns the conversation history. This is useful when you need to redact, summarize, or store only part of the transcript before the next request.

## 3. Check your work

- You continued a thread with `previous_response_id`
- You ran the same two-turn flow with `store=False` and manual history
- You understand that "stateless" and "stateful" are implementation choices, not separate model families
