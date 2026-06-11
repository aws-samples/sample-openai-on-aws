---
title: "Structured Data Extraction"
weight: 3
---

## 1. Why this matters

The real power of vision isn't getting a text summary, it's extracting structured data you can feed into downstream systems. A FinOps pipeline that reads Cost Explorer screenshots and outputs JSON can automatically populate Slack alerts, update dashboards, or trigger budget workflows. This is the same pattern used in Intelligent Document Processing (IDP) for invoices, forms, and receipts.

GPT-5.4 can combine vision with structured output (`text.format`) in one request. Depending on the accuracy requirements, you may still choose to validate values or pair the model with specialized OCR, but the single-request pattern is useful for many first-pass extraction workflows.

## 2. What this code does

Sends the same Cost Explorer image but requests the output as structured JSON. The model reads the visual data and returns it in a machine-parseable format you can pipe directly into other systems.

## 3. Run it

Copy the below code to a file `vision_extract.py`:

```python
import os, base64, pathlib, json
from openai import OpenAI


img_path = pathlib.Path("cost_explorer.png")
if not img_path.exists():
    raise FileNotFoundError("Save the sample dashboard image as cost_explorer.png in this folder, or update img_path to your image file.")

b64 = base64.b64encode(img_path.read_bytes()).decode()

client = OpenAI()

response = client.responses.create(
    model=os.environ["MODEL_ID"],
    instructions="You are a FinOps data extraction system. Extract cost data from dashboard screenshots into structured JSON.",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Extract all visible cost data from this dashboard. Return JSON with keys: total_current_month, total_previous_month, cost_difference, cost_difference_percent, and services (array of {name, current_month_cost, previous_month_cost, change_percent})."},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}
        ]
    }],
    text={"format": {"type": "json_object"}}
)

# Parse and pretty-print the structured output
data = json.loads(response.output_text)
print(json.dumps(data, indent=2))

# Example: use the extracted data programmatically
print(f"\nTotal cost change: {data.get('cost_difference', 'N/A')}")
print(f"Top service: {data.get('services', [{}])[0].get('name', 'N/A')}")
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 vision_extract.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python vision_extract.py
:::
::::
:::::

## 4. Understanding the output

You get machine-readable JSON from the visual chart, not a text summary, but structured data. Validate exact values before using them in financial reporting or compliance workflows. This is the building block for:
- Automated cost reports that run on a schedule
- Slack alerts when a service exceeds a threshold
- Data pipelines that compare screenshots over time
- Audit trails that capture point-in-time cost snapshots

The `text={"format": {"type": "json_object"}}` parameter asks the model to return valid JSON. Without it, the model might wrap the JSON in markdown code fences or add explanatory text around it.

---

## 5. Typed extraction with Pydantic

For production pipelines, you want type safety — not just raw JSON. The OpenAI SDK's `.parse()` method validates the response against a Pydantic model, giving you typed Python objects with IDE autocomplete and runtime validation.

Install pydantic if you don't have it:

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

Copy the below code to a file `vision_extract_typed.py`:

```python
import os, base64, pathlib, json
from pydantic import BaseModel
from openai import OpenAI

class ServiceCost(BaseModel):
    name: str
    current_month_cost: float
    previous_month_cost: float

class CostReport(BaseModel):
    total_current_month: float
    total_previous_month: float
    services: list[ServiceCost]

img_path = pathlib.Path("cost_explorer.png")
if not img_path.exists():
    raise FileNotFoundError("Save the sample dashboard image as cost_explorer.png in this folder, or update img_path to your image file.")

b64 = base64.b64encode(img_path.read_bytes()).decode()

client = OpenAI()

response = client.responses.parse(
    model=os.environ["MODEL_ID"],
    instructions="Extract cost data from this dashboard screenshot.",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Extract all visible service costs from this dashboard."},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}
        ]
    }],
    text_format=CostReport,
)

report = response.output_parsed
print(f"Current month total: ${report.total_current_month:,.2f}")
print(f"Previous month total: ${report.total_previous_month:,.2f}")
print(f"\nServices extracted: {len(report.services)}")
for svc in report.services[:5]:
    print(f"  {svc.name}: ${svc.current_month_cost:,.2f} -> ${svc.previous_month_cost:,.2f}")
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 vision_extract_typed.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python vision_extract_typed.py
:::
::::
:::::

The key difference: `response.output_parsed` gives you a `CostReport` object — not a dict you have to validate manually. If the model returns data that doesn't match your schema, pydantic raises a validation error immediately rather than failing silently downstream.
