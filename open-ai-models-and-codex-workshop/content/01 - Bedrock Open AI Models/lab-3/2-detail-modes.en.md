---
title: "Detail Modes"
weight: 2
---

## 1. Why this matters

Production dashboards often have tiny axis labels, dense legends, and small-font annotations that carry critical information. A model that misreads "$3,600" as "$3,000" produces a wrong cost report. The image `detail` setting lets you trade latency and token cost for better handling of fine-grained visual details.

For workshop purposes, use `auto` for quick analysis and `high` when small text or dense chart labels matter. Even at higher detail, treat extracted values as model output that should be validated before it drives financial or compliance decisions.

## 2. What this code does

Sends the same image twice with different `detail` settings and asks the model to read specific small numbers from the chart. You'll compare whether higher detail improves small-text extraction for your image.

## 3. Run it

Copy the below code to a file `vision_detail.py`:

```python
import os, base64, pathlib
from openai import OpenAI


img_path = pathlib.Path("cost_explorer.png")
if not img_path.exists():
    raise FileNotFoundError("Save the sample dashboard image as cost_explorer.png in this folder, or update img_path to your image file.")

b64 = base64.b64encode(img_path.read_bytes()).decode()

client = OpenAI()

question = "Read the exact dollar amounts for each service shown in the bar chart. List each service name and its cost for both months shown."

# Auto mode (default, faster, may approximate small text)
print("=== detail: auto ===\n")
response_auto = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": question},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "auto"}
        ]
    }]
)
print(response_auto.output_text)

# High mode (higher detail, slower, often better for tiny text)
print("\n=== detail: high ===\n")
response_orig = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": question},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"}
        ]
    }]
)
print(response_orig.output_text)
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 vision_detail.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python vision_detail.py
:::
::::
:::::

## 4. Understanding the output

Compare the two responses. With `auto`, the model may round numbers or miss small labels. With `high`, it often has a better chance of reading fine details, but you should still verify exact values against the source image. The tradeoff: `high` uses more input tokens (higher cost) and takes slightly longer.

**When to use each:**
- `auto` — quick analysis, summaries, identifying trends (most use cases)
- `high` — financial data extraction, compliance documents, handwritten forms, or any image where small text matters
