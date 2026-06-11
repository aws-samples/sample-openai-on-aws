---
title: "Analyze a Cost Dashboard"
weight: 1
---

## 1. Why this matters

FinOps teams spend hours manually reviewing cost dashboards and writing summaries for leadership. With vision, you can automate the first pass: feed a dashboard screenshot to GPT-5.4 and get a plain-English analysis in seconds. This is the same pattern used in production for automated reporting, anomaly detection, and executive briefing generation.

## 2. What this code does

The script loads your local screenshot, base64-encodes it, and sends it as part of a multi-part content array alongside a text prompt. The Responses API can also accept a fully qualified image URL or a file ID, but base64 is convenient for local screenshots because you do not need to upload the file anywhere first.

## 3. Run it

Before creating the script, confirm the image file is in your current folder:

```console
ls cost_explorer.png
```

If this command fails, go back to the Lab 3 overview page and save the sample dashboard image locally as `cost_explorer.png`.

Copy the below code to a file `vision_analyze.py`:

```python
import os, base64, pathlib
from openai import OpenAI


# Load your screenshot
img_path = pathlib.Path("cost_explorer.png")
if not img_path.exists():
    raise FileNotFoundError("Save the sample dashboard image as cost_explorer.png in this folder, or update img_path to your image file.")

b64 = base64.b64encode(img_path.read_bytes()).decode()

client = OpenAI()

response = client.responses.create(
    model=os.environ["MODEL_ID"],
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Analyze this AWS Cost Explorer dashboard. Identify the top cost drivers, month-over-month trends, and any services that warrant attention."},
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}
        ]
    }]
)

print(response.output_text)
```

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 vision_analyze.py
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python vision_analyze.py
:::
::::
:::::

## 4. Understanding the output

The model reads the bar chart, the cost comparison numbers, and the driver cards, then synthesizes a coherent analysis. Notice it doesn't just OCR the text; it interprets the visual relationships (which bars are taller, which trends are concerning) the same way a human would when glancing at a dashboard.

## 5. Key API pattern

The content array uses typed blocks:
- `{"type": "input_text", "text": "..."}` for your prompt
- `{"type": "input_image", "image_url": "data:image/png;base64,..."}` for the image

This is different from Labs 1 and 2 where `input` was just a string or a list of message objects with text content only.
