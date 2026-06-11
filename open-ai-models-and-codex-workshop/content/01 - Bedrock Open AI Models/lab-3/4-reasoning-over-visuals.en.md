---
title: "Reasoning Over Visual Data"
weight: 4
---

## 1. Why this matters

Reading numbers from a chart is perception. Answering "which service should I investigate first given these trends?" is reasoning. Production FinOps workflows need both: extract the data AND draw conclusions that require combining multiple data points, comparing ratios, and projecting trends.

GPT-5.4's `reasoning` parameter lets you request more or less reasoning effort after the model perceives the image. At `effort: "low"`, it should answer quickly and may stay closer to surface-level observations. At `effort: "medium"`, it can spend more effort comparing services, calculating ratios, and producing deeper analysis.

## 2. What this code does

Asks a compositional question that requires the model to combine multiple pieces of visual information, then compares the output at different reasoning effort levels.

## 3. Run it

Copy the below code to a file `vision_reasoning.py`:

```python
import os, base64, pathlib
from openai import OpenAI


img_path = pathlib.Path("cost_explorer.png")
if not img_path.exists():
    raise FileNotFoundError("Save the sample dashboard image as cost_explorer.png in this folder, or update img_path to your image file.")

b64 = base64.b64encode(img_path.read_bytes()).decode()

client = OpenAI()

complex_question = """Based on this cost dashboard:
1. Which service has the highest absolute cost but lowest percentage change?
2. If current month-over-month trends continue for 3 months, which service will overtake another in total spend?
3. What is the ratio of the top service's cost to the combined cost of the bottom 5 services?
4. Recommend which service to investigate first for cost optimization and explain why."""

# Low reasoning effort - quick surface-level answer
print("=== reasoning effort: low ===\n")
response_low = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": complex_question},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}
        ]
    }],
    reasoning={"effort": "low"}
)
print(response_low.output_text)

# Medium reasoning effort - deeper multi-step analysis
print("\n=== reasoning effort: medium ===\n")
response_med = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": complex_question},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}
        ]
    }],
    reasoning={"effort": "medium"}
)
print(response_med.output_text)
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 vision_reasoning.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python vision_reasoning.py
:::
::::
:::::

## 4. Understanding the output

Compare the two responses:
- **effort: low** — answers quickly, may skip calculations or give approximate answers to the multi-step questions
- **effort: medium** — often shows deeper analysis, attempts ratio calculations, projects trends, and provides reasoned recommendations

The tradeoff is latency and token cost. For a quick "what's my top cost driver?" question, `low` is fine. For "analyze this dashboard and produce an executive briefing with recommendations," use `medium`.

**Production pattern:** Use `low` for real-time alerts and quick checks. Use `medium` for scheduled reports, audit analysis, and anything going to leadership.

:::alert{header="Vision accuracy limitations" type="warning"}
GPT-5.4 may approximate percentages and derived calculations even at high reasoning effort — it's reading pixels, not querying a database. For production workflows where exact numbers matter (financial reporting, compliance), use vision to *extract* the raw values, then do the math in your application code. Treat vision output as OCR-quality input, not as a calculator.
:::

## 5. Check your work

- You sent an image to GPT-5.4 and received a plain-English analysis
- You compared `detail: auto` vs `detail: high` and saw the accuracy difference
- You extracted structured JSON from a visual dashboard in a single API call
- You used `reasoning.effort` to control analysis depth on visual data

These four controls (`detail`, `verbosity`, `reasoning.effort`, `text.format`) are useful building blocks for production-style vision workflows. Each one gives you a knob to tune the accuracy/cost/latency tradeoff for your specific workload.
