---
title: "Multiple Tools and Parallel Calls"
weight: 3
---

Real applications don't have just one tool. In this exercise, you'll define multiple tools, see how the model routes questions, control tool selection with `tool_choice`, and handle parallel tool calls.

## 1. Tool routing

The model reads each question, compares it against the available tool descriptions, and picks the best match by default. You can still influence or constrain this behavior with `tool_choice` when your application needs a specific pattern.

Copy the below code to a file `function_call_multi.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City and state"}
            },
            "required": ["location"]
        }
    },
    {
        "type": "function",
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol, e.g. AMZN"}
            },
            "required": ["ticker"]
        }
    },
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": "Search an internal knowledge base for company policies and procedures.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
    }
]

# The model picks the right tool for each question
questions = [
    "What's the weather in New York?",
    "What's Amazon's stock price?",
    "What is our company's PTO policy?",
]

for question in questions:
    response = client.responses.create(
        model=os.environ["MODEL_ID"],
        input=question,
        tools=tools
    )

    for item in response.output:
        if item.type == "function_call":
            print(f"Q: {question}")
            print(f"   -> {item.name}({item.arguments})\n")
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 function_call_multi.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python function_call_multi.py
:::
::::
:::::

---

## 2. Controlling tool selection with `tool_choice`

By default, the model decides whether to use a tool (`tool_choice="auto"`). You can override this:

| Value | Behavior |
|-------|----------|
| `"auto"` | Model decides whether to call a tool (default) |
| `"required"` | Model must call at least one tool |
| `"none"` | Model must NOT call any tools. Answer directly |
| `{"type": "function", "name": "get_weather"}` | Force a specific tool |

Copy the below code to a file `tool_choice_demo.py`:

```python
import os
from openai import OpenAI

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    }
]

# Force the model to NOT use tools. Answer from its own knowledge.
print("=== tool_choice: none ===\n")
response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="What's the weather in Seattle?",
    tools=tools,
    tool_choice="none"
)
print(response.output_text)

# Force the model to use a tool even for a question it could answer directly
print("\n=== tool_choice: required ===\n")
response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="Tell me a joke about the weather.",
    tools=tools,
    tool_choice="required"
)
for item in response.output:
    if item.type == "function_call":
        print(f"Forced tool call: {item.name}({item.arguments})")
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 tool_choice_demo.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python tool_choice_demo.py
:::
::::
:::::

---

## 3. Parallel tool calls

When a question requires data from multiple independent sources, the model can call several tools in the same turn. This is faster than sequential calls because you can execute them concurrently.

Copy the below code to a file `parallel_tools.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    },
    {
        "type": "function",
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol.",
        "parameters": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"]
        }
    }
]

# Ask a question that requires BOTH tools
response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="What's the weather in New York and what's Apple's stock price?",
    tools=tools
)

# The model returns multiple function calls in one response
function_calls = [item for item in response.output if item.type == "function_call"]
print(f"Model made {len(function_calls)} parallel tool calls:\n")
for fc in function_calls:
    print(f"  {fc.name}({fc.arguments})")

# Execute all calls (in production you'd do this concurrently)
results = {}
for fc in function_calls:
    if fc.name == "get_weather":
        results[fc.call_id] = json.dumps({"temperature": 72, "condition": "Sunny"})
    elif fc.name == "get_stock_price":
        results[fc.call_id] = json.dumps({"ticker": "AAPL", "price": 198.50})

# Send all results back at once
input_items = [{"role": "user", "content": "What's the weather in New York and what's Apple's stock price?"}]
for fc in function_calls:
    input_items.append({"type": "function_call", "name": fc.name, "arguments": fc.arguments, "call_id": fc.call_id})
    input_items.append({"type": "function_call_output", "call_id": fc.call_id, "output": results[fc.call_id]})

final = client.responses.create(model=os.environ["MODEL_ID"], input=input_items, tools=tools)
print(f"\nFinal answer:\n{final.output_text}")
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 parallel_tools.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python parallel_tools.py
:::
::::
:::::

The model recognized both sub-questions were independent and issued both tool calls in a single turn. In production, you'd execute these concurrently (e.g., with `asyncio.gather`) for lower latency.
