---
title: "Function Calling: The Tool Use Loop"
weight: 1
---

In this exercise, you'll define a tool, trigger a function call, execute it, and return the result. That is the complete tool use cycle in one script.

This is the key difference from Lab 1: the model recognizes it doesn't have the information needed (live weather data) and explicitly asks your code to fetch it rather than making something up.

## 1. How the tool use loop works

1. **Send the prompt with tool definitions.** Tell the model what tools are available.
2. **Model returns a `function_call`.** It chose a tool and extracted arguments from your question.
3. **You execute the function.** Call your API, database, or service.
4. **Send the result back.** Pass the function output back to the model.
5. **Model generates the final answer.** It now has the data it needs.

## 2. Run it

Copy the below code to a file `function_call_loop.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

# Define the tool
weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City and state, e.g. Seattle, WA"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit"}
        },
        "required": ["location"]
    }
}

# Step 1: Send the prompt with tool definitions
print("Step 1: Sending prompt with tool definition...\n")
response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input="What's the weather like in Seattle today?",
    tools=[weather_tool]
)

# Step 2: Check if the model wants to call a function
function_call = next((item for item in response.output if item.type == "function_call"), None)

if function_call:
    print(f"Step 2: Model wants to call: {function_call.name}({function_call.arguments})")
    print(f"        Call ID: {function_call.call_id}\n")

    # Step 3: Execute the function (simulated here, in production this calls a real API)
    weather_data = json.dumps({
        "temperature": 58,
        "condition": "Partly cloudy",
        "humidity": "72%",
        "unit": "fahrenheit"
    })
    print(f"Step 3: Executed function, got: {weather_data}\n")

    # Step 4: Send the result back to the model
    final_response = client.responses.create(
        model=os.environ["MODEL_ID"],
        input=[
            {"role": "user", "content": "What's the weather like in Seattle today?"},
            {
                "type": "function_call",
                "name": function_call.name,
                "arguments": function_call.arguments,
                "call_id": function_call.call_id
            },
            {
                "type": "function_call_output",
                "call_id": function_call.call_id,
                "output": weather_data
            }
        ],
        tools=[weather_tool]
    )

    # Step 5: Print the final answer
    print(f"Step 5: Final answer:\n{final_response.output_text}")
else:
    print(f"Model answered directly: {response.output_text}")
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 function_call_loop.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python function_call_loop.py
:::
::::
:::::

## 3. What you should see

```
Step 1: Sending prompt with tool definition...

Step 2: Model wants to call: get_weather({"location":"Seattle, WA","unit":"fahrenheit"})
        Call ID: call_0

Step 3: Executed function, got: {"temperature": 58, "condition": "Partly cloudy", "humidity": "72%", "unit": "fahrenheit"}

Step 5: Final answer:
Seattle is 58°F and partly cloudy today, with humidity around 72%.
```

## 4. Understanding the output

- **Step 2**: The model didn't answer directly. It returned a `function_call` with the tool name and extracted arguments.
- **Step 3**: You executed the function (simulated here, real API in production).
- **Step 5**: After receiving the function output, the model wove the data into a natural language response.

The model didn't just parrot back the JSON. It interpreted `"temperature": 58, "condition": "Partly cloudy"` and presented it conversationally. Your code handles data retrieval; the model handles presentation.
