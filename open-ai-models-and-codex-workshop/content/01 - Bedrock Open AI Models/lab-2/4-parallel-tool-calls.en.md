---
title: "Parallel Tool Calls"
weight: 4
---

When a question requires the same tool for multiple independent inputs, the model doesn't wait. It fires all the calls at once in a single response. This is **parallel tool calling**, and it's the default behavior when the model determines the calls don't depend on each other.

## 1. What this code does

The script asks about weather in three cities at once. Because none of those lookups depend on each other, the model returns all three `function_call` items in a single response, one turn instead of three. Your code executes all three, returns all results, and the model writes a single final answer.

Compare this to a sequential tool loop where one call's output is needed before the next call can be planned. Weather for three cities is parallel by nature.

## 2. Run it

Copy the below code to a file `function_call_parallel.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["city"]
    }
}

# Step 1: Ask about three cities. Model fires all three calls in one turn.
response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="I'm visiting Seattle, New York, and Miami next week. What's the weather like in each city?",
    tools=[weather_tool]
)

function_calls = [item for item in response.output if item.type == "function_call"]
print(f"Model made {len(function_calls)} call(s) in one turn:")
for fc in function_calls:
    print(f"  -> {fc.name}({fc.arguments})")

# Simulated weather data
weather_data = {
    "Seattle":  {"temp": 55, "condition": "Rainy",                  "unit": "fahrenheit"},
    "New York": {"temp": 72, "condition": "Sunny",                   "unit": "fahrenheit"},
    "Miami":    {"temp": 88, "condition": "Humid and partly cloudy", "unit": "fahrenheit"},
}

# Step 2: Execute all calls and build the full input for the next turn
input_items = [
    {"role": "user", "content": "I'm visiting Seattle, New York, and Miami next week. What's the weather like in each city?"}
]

for fc in function_calls:
    args = json.loads(fc.arguments)
    city = args.get("city", "").split(",")[0].strip()
    result = json.dumps(weather_data.get(city, {"error": "not found"}))

    input_items.append({
        "type": "function_call",
        "name": fc.name,
        "arguments": fc.arguments,
        "call_id": fc.call_id
    })
    input_items.append({
        "type": "function_call_output",
        "call_id": fc.call_id,
        "output": result
    })

# Step 3: Send all results back. Model writes a single final answer.
final = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=input_items,
    tools=[weather_tool]
)

print(f"\nFinal answer:\n{final.output_text}")
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 function_call_parallel.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python function_call_parallel.py
:::
::::
:::::

## 3. What you should see

```text
Model made 3 call(s) in one turn:
  -> get_weather({"city":"Seattle","unit":"fahrenheit"})
  -> get_weather({"city":"New York","unit":"fahrenheit"})
  -> get_weather({"city":"Miami","unit":"fahrenheit"})

Final answer:
Here's the forecast for next week:

- Seattle: 55F, rainy
- New York: 72F, sunny
- Miami: 88F, humid and partly cloudy
```

## 4. Understanding the output

The model issued all three `get_weather` calls in a **single response** rather than one at a time. This matters in production: three sequential calls would take 3x the latency of a single round-trip. With parallel calls, all three execute simultaneously and you get one final answer.

Key things to notice in the code:

- `function_calls` is a list, so iterate over it so your code handles one or many calls
- Every `function_call` item in the input array needs a matching `function_call_output` with the same `call_id` before the model will respond
- The order you add them to `input_items` doesn't matter. The `call_id` is what links them

:::alert{header="When does the model parallelize?" type="info"}
The model decides based on data dependencies. If the calls are independent (weather in three cities, stock prices for three tickers), it parallelizes. If one call's output determines the next call's inputs (look up a customer, then look up their orders), it sequences. You can override this with `parallel_tool_calls=False` to force sequential execution.
:::
