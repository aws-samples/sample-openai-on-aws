---
title: "Structured Outputs"
weight: 5
---

Structured Outputs lets you constrain the model's response to a specific format - either valid JSON, or a strict schema your code can parse directly. This eliminates brittle string parsing and makes model output safe to use in data pipelines, APIs, and typed systems.

There are two modes:

| Mode | What it does |
|------|-------------|
| `json_object` | Requests valid JSON - no schema enforcement |
| `json_schema` | Constrains output to valid JSON that matches your schema |

---

## 1. JSON Mode

Pass `text={"format": {"type": "json_object"}}` and the model returns valid JSON. No schema required - useful when you want structured output but don't need strict field control.

Copy the below code to a file `structured_json_mode.py`:

```python
import json
import os
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model=os.environ["MODEL_ID"],
    instructions="Always respond with valid JSON.",
    input="Give me the name, founded year, and headquarters of Amazon.",
    text={"format": {"type": "json_object"}}
)

data = json.loads(response.output_text)
print(json.dumps(data, indent=2))
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 structured_json_mode.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python structured_json_mode.py
:::
::::
:::::

---

## 2. Structured Outputs with Pydantic

The cleaner approach: define your schema as a Pydantic model and use `responses.parse()`. The SDK validates the response and returns a typed Python object - no `json.loads()`, no key lookups.

If you do not already have Pydantic installed, install it:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 -m pip install pydantic
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python -m pip install pydantic
:::
::::
:::::

Copy the below code to a file `structured_pydantic.py`:

```python
import os
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class SupportTicket(BaseModel):
    category: str
    severity: str
    summary: str

response = client.responses.parse(
    model=os.environ["MODEL_ID"],
    input="My EC2 instance is down and I can't SSH in.",
    text_format=SupportTicket,
)

ticket = response.output_parsed
print(f"Category: {ticket.category}")
print(f"Severity: {ticket.severity}")
print(f"Summary:  {ticket.summary}")
```

Now execute the file:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 structured_pydantic.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python structured_pydantic.py
:::
::::
:::::

`response.output_parsed` is a `SupportTicket` instance - fully typed, IDE-autocompletable, no parsing needed.

---

## 3. Try it yourself

The same pattern handles more complex schemas. A few things to try:

- **Nested objects** - add a `location` field that's itself an object with `city` and `country` fields. Does the model populate both from context?
- **Arrays** - ask for a list of 5 AWS services, each with `name` and `one_line_description`. Use `list[Service]` in Pydantic or an `array` of objects in json_schema.
- **Enums** - constrain `severity` to `"low" | "medium" | "high" | "critical"` using `from typing import Literal`. Schema validation keeps downstream code from accepting values outside the declared set.

:::alert{header="Tip" type="info"}
If a required field has no data in the input (e.g. `country` when the input only mentions a city), the model may still need to provide a value to satisfy the schema. Design your schemas to include nullable fields or explicit `"unknown"` values when missing information is possible.
:::

## 4. Check your work

- You received valid JSON from `json_object` mode
- You got a typed Python object from `responses.parse()` with Pydantic
- You understand the difference between JSON mode (valid JSON) and json_schema (schema-enforced JSON)
