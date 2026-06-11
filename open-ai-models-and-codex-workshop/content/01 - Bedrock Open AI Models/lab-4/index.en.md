---
title: "Lab 4: Agents SDK"
weight: 40
---

In Lab 2, you built the tool use loop manually — detect function calls, execute them, feed results back. That works, but gets complex when questions require multiple sequential tool calls across many turns.

The [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) automates this entire loop. You define tools with decorators and the SDK handles orchestration, multi-turn execution, agent handoffs, and run history.

In this lab you'll first build a manual agent loop to see what the SDK automates, then rewrite it with the SDK.

**Time:** ~20 minutes **Prerequisites:** Lab 2 complete

---

## 1. Build a Manual Agent Loop

This script implements a multi-turn agent loop that handles sequential tool calls — the same pattern the Agents SDK automates for you.

Copy the below code to a file `manual_agent_loop.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

# Simulated tool implementations
def get_order_status(order_id):
    orders = {
        "ORD-001": {"status": "shipped", "eta": "2025-03-15", "carrier": "UPS"},
        "ORD-002": {"status": "processing", "eta": "2025-03-18", "carrier": "pending"},
    }
    return json.dumps(orders.get(order_id, {"error": "Order not found"}))

def get_customer_info(customer_id):
    customers = {
        "CUST-100": {"name": "Alice Johnson", "plan": "enterprise", "orders": ["ORD-001", "ORD-002"]},
    }
    return json.dumps(customers.get(customer_id, {"error": "Customer not found"}))

# Map function names to implementations
tool_handlers = {
    "get_order_status": lambda args: get_order_status(args["order_id"]),
    "get_customer_info": lambda args: get_customer_info(args["customer_id"]),
}

tools = [
    {
        "type": "function",
        "name": "get_order_status",
        "description": "Get the shipping status of an order by order ID.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID like ORD-001"}},
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "get_customer_info",
        "description": "Get customer details including name, plan, and order history.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "description": "Customer ID like CUST-100"}},
            "required": ["customer_id"]
        }
    }
]

# The agent loop
input_items = [{"role": "user", "content": "Look up customer CUST-100 and tell me the status of all their orders."}]

print("=== Manual Agent Loop ===\n")
for turn in range(5):  # Max 5 turns to prevent infinite loops
    response = client.responses.create(
        model=os.environ["MODEL_ID"],
        input=input_items,
        tools=tools
    )

    function_calls = [item for item in response.output if item.type == "function_call"]

    if not function_calls:
        print(f"\n=== Final Answer ===\n\n{response.output_text}")
        break

    for fc in function_calls:
        args = json.loads(fc.arguments)
        result = tool_handlers[fc.name](args)
        print(f"  Turn {turn + 1}: {fc.name}({json.dumps(args)}) -> {result[:80]}")

        input_items.append({"type": "function_call", "name": fc.name, "arguments": fc.arguments, "call_id": fc.call_id})
        input_items.append({"type": "function_call_output", "call_id": fc.call_id, "output": result})
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 manual_agent_loop.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python manual_agent_loop.py
:::
::::
:::::

Notice how much boilerplate this requires: the loop, the function dispatch, rebuilding the input list, handling the termination condition. The Agents SDK eliminates all of this.

---

## 2. Install the Agents SDK

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 -m pip install openai-agents
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python -m pip install openai-agents
:::
::::
:::::

---

## 3. The Same Thing with the Agents SDK

Now rewrite the exact same agent using the SDK. The tool definitions become decorators, and the loop disappears entirely.

Copy the below code to a file `agents_with_tools.py`:

```python
import asyncio
import json
import os
from agents import Agent, Runner, function_tool, set_tracing_disabled

# The Agents SDK reads OPENAI_BASE_URL and OPENAI_API_KEY from your environment,
# so it talks to Bedrock just like the OpenAI client did in the earlier labs.
# Tracing is disabled because it would otherwise try to upload run data to
# OpenAI's platform using your Bedrock token.
set_tracing_disabled(True)


@function_tool
def get_customer_info(customer_id: str) -> str:
    """Get customer details including name, plan, and order history."""
    customers = {
        "CUST-100": {"name": "Alice Johnson", "plan": "enterprise", "orders": ["ORD-001", "ORD-002"]},
    }
    return json.dumps(customers.get(customer_id, {"error": "Customer not found"}))


@function_tool
def get_order_status(order_id: str) -> str:
    """Get the shipping status of an order by order ID."""
    orders = {
        "ORD-001": {"status": "shipped", "eta": "2025-03-15", "carrier": "UPS"},
        "ORD-002": {"status": "processing", "eta": "2025-03-18", "carrier": "pending"},
    }
    return json.dumps(orders.get(order_id, {"error": "Order not found"}))


agent = Agent(
    name="Customer Support",
    instructions="You help look up customer information and order statuses.",
    model=os.environ["MODEL_ID"],
    tools=[get_customer_info, get_order_status],
)


async def main():
    result = await Runner.run(agent, "Look up customer CUST-100 and tell me the status of all their orders.")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 agents_with_tools.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python agents_with_tools.py
:::
::::
:::::

Same question, same tools, same answer — but no loop, no dispatch, no input management. The SDK handled all of it.

---

## 4. Agent Handoffs

Multiple agents can collaborate, with one handing off to another based on the user's needs.

Copy the below code to a file `agents_handoff.py`:

```python
import asyncio
import os
from agents import Agent, Runner, set_tracing_disabled

set_tracing_disabled(True)

security_agent = Agent(
    name="Security Specialist",
    instructions="You are an AWS security expert. Focus on IAM, encryption, and compliance.",
    model=os.environ["MODEL_ID"],
)

cost_agent = Agent(
    name="Cost Optimizer",
    instructions="You are an AWS cost optimization expert. Focus on pricing, reserved capacity, and savings plans.",
    model=os.environ["MODEL_ID"],
)

triage_agent = Agent(
    name="Triage",
    instructions="You route questions to the right specialist. Hand off security questions to the Security Specialist and cost questions to the Cost Optimizer.",
    model=os.environ["MODEL_ID"],
    handoffs=[security_agent, cost_agent],
)


async def main():
    result = await Runner.run(triage_agent, "How can I reduce my monthly S3 bill by 40%?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 agents_handoff.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python agents_handoff.py
:::
::::
:::::

The triage agent recognized this as a cost question and handed off to the Cost Optimizer. Try asking a security question instead and see it route differently.

---

## 5. Check your work

- ☑ You built a manual agent loop and saw the boilerplate required
- ☑ You rewrote the same agent with the SDK and saw the code shrink dramatically
- ☑ You set up agent handoffs and saw routing between specialists
