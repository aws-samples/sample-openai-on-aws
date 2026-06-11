---
title: "OpenAI SDK (Python)"
weight: 1
---

The OpenAI Python SDK is the simplest way to interact with GPT-5.5 programmatically. The SDK reads the environment variables you configured in Getting Started (`OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `MODEL_ID`).

**Time:** ~15 minutes 
**Prerequisites:** OpenAI SDK installed, and `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `MODEL_ID` set from Getting Started

---

## 1. Responses API

The Responses API is OpenAI's modern inference interface: tool-capable, items-based, and able to support both independent requests and stateful multi-turn patterns.

### Create a Basic Response

Copy the below code to a file `openai_basic_response.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[
        {"role": "user", "content": "Hello! How can you help me today?"}
    ]
)

print(response.output_text)
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 openai_basic_response.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python openai_basic_response.py
:::
::::
:::::

---

### Multi-Turn Conversation

The Responses API is stateful by default. Each response is stored server-side and can be referenced by ID in follow-up requests, so you don't need to resend the full conversation history.

Copy the below code to a file `openai_multi_turn.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

# First turn
response1 = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="What is the capital of France?",
    store=True
)
print(f"Turn 1: {response1.output_text}")

# Follow-up: the server recalls the full conversation context
response2 = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="What is its population?",
    previous_response_id=response1.id,
    store=True
)
print(f"Turn 2: {response2.output_text}")
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 openai_multi_turn.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python openai_multi_turn.py
:::
::::
:::::

Note that `store=True` is the default, so you can omit it.

---

### Create a Streaming Response

To stream the response, pass `stream=True` as an additional parameter.

Copy the below code to a file `openai_stream_response.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

stream = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[
        {"role": "user", "content": "Hello! How can you help me today?"}
    ],
    stream=True
)

for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)

print()
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 openai_stream_response.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python openai_stream_response.py
:::
::::
:::::

---

## 2. Check your work

- ☑ You created a basic response using the Responses API
- ☑ You used `previous_response_id` to continue a conversation without resending history
- ☑ You streamed a response and saw tokens appear progressively
