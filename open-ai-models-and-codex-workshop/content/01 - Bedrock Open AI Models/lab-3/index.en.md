---
title: "Lab 3: Vision"
weight: 30
---

GPT-5.4 supports image inputs through the Responses API, making it useful for first-pass analysis of dashboards, documents, architecture diagrams, and monitoring screenshots. Vision output should still be validated when exact numbers matter, but it can remove a lot of manual review from workflows such as cost analysis, document processing, infrastructure diagram review, and monitoring triage.

In this lab you'll use your own AWS Cost Explorer dashboard as the input image and progressively apply Responses API controls to extract increasingly sophisticated insights from it.

**Time:** ~15 minutes **Prerequisites:** Lab 1 complete

---

## 1. Required: save an image locally first

Before running any Vision lab script, you must have a local image file named `cost_explorer.png` in the same folder where you create the Python files. The sample dashboard below is served by Workshop Studio so you can see and download it, but the Python scripts cannot read the browser-rendered image automatically.

:::alert{type="warning" header="Do this before running the code"}
Right-click the sample image below, save it as `cost_explorer.png`, and place it in the directory where you will run `python vision_analyze.py`. If you use your own screenshot, rename it to `cost_explorer.png` or update `img_path` in each script.
:::

**Option A: Download the sample dashboard image**

Right-click the image below and save it as `cost_explorer.png` in your working directory:

![Sample AWS Cost Explorer dashboard showing month-over-month spending by service](/static/images/part1/cost-explorer-reference.png)


**Option B: Use your own image**

Any screenshot or image containing text and data works — an architecture diagram, a monitoring dashboard, or your OpenAI usage page. Save it as `cost_explorer.png` in your working directory (or update the filename in the exercises).

Confirm the file is in the right place before running the scripts:

```console
ls cost_explorer.png
```

If the command prints `cost_explorer.png`, you are ready. If it says `No such file or directory`, move into the folder where you saved the image or save the image again in your current working directory.

---

## 2. Useful controls for vision workflows

The Responses API gives you several controls that help tune vision workflows:

| Parameter | What it does | When to use it |
|-----------|-------------|----------------|
| `detail="auto"` | Default resolution processing | Most pages, clear text |
| `detail="high"` | Higher-detail image processing | Tiny text, dense data, handwriting |
| `text={"verbosity": "high"}` | Faithful transcription mode | OCR-style extraction, preserving layout |
| `reasoning={"effort": "high"}` | Multi-step visual reasoning | Charts, tables, spatial relationships |
| `text={"format": {"type": "json_object"}}` | Structured extraction from images | Data pipelines, IDP workflows |

Together, these controls help you balance accuracy, latency, and cost for the workload in front of you.
