---
title: "Work with images and multimodal inputs"
weight: 32
---

:::alert{type="info" header="Image inputs work on Bedrock"}
Codex reads local image files and sends them inline (base64), which Bedrock accepts. Image *generation* is a different story: it is a hosted capability that is not available on the Bedrock path, so the generate-images flow below is shown for reference only.
:::

Codex can process images to help with debugging, implementing designs, and understanding visual content.

## 1. Attach images from command line

Single image:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex -i screenshot.png "Explain this error"
:::

Multiple images:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex --image design.png,mockup.png "Compare these UI designs"
:::

## 2. Attach images in session

Use the :code[/mention]{showCopyAction=false} command:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/mention screenshot.png
:::

Or drag and drop images directly into the composer.

## 3. Use cases for image inputs

| Input Type | Example Prompt |
|:-----------|:---------------|
| Error screenshot | "Fix this error shown in the screenshot" |
| UI mockup | "Implement this design in React" |
| Architecture diagram | "Explain this system architecture" |
| Database schema | "Generate models based on this ERD" |

## 4. Generate images (not available on Bedrock)

On the standard OpenAI path, Codex can create images with :code[$imagegen]{showCopyAction=false}:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Create a logo for my FastAPI project $imagegen
:::

:::alert{type="warning" header="Unavailable on the Bedrock path"}
Image generation is a hosted capability that the `amazon-bedrock` provider does not support, so this command will not work in this workshop. Image *inputs* (sections 1 through 3) work normally.
:::

## 5. Congratulations!

You can now use images as input with Codex on Bedrock.
