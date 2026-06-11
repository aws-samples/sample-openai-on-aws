---
title: "OpenAI CLI"
weight: 4
---

In this module, you will use the OpenAI CLI to interact with GPT-5.4 from your terminal. The CLI talks to the same Bedrock endpoint as the SDK. It reads `OPENAI_BASE_URL` and `OPENAI_API_KEY` from your environment, so the commands below look identical to vanilla OpenAI usage.

**Time:** ~10 minutes
**Prerequisites:** `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `MODEL_ID` set from Getting Started

---

## 1. Install the OpenAI CLI

The OpenAI CLI is a Go binary installed via Homebrew (macOS and Linux/WSL). Do not use the Python `openai-cli` package. That is a legacy tool that does not support the Responses API.

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
brew tap openai/tools
brew install openai
:::

:::alert{header="Windows users" type="info"}
If you're on Windows, use WSL (as noted in the prerequisites) and run the brew commands above. Alternatively, download the binary directly from the [OpenAI CLI GitHub releases](https://github.com/openai/openai-cli/releases) page.
:::

Verify the installation:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
openai --version
:::

:::alert{header="Conflict with Python openai-cli" type="warning"}
If you previously installed `openai-cli` via pip, it may shadow the Homebrew binary. Remove it first: `pip uninstall openai-cli -y`, then ensure `which openai` points to `/opt/homebrew/bin/openai`.
:::

---

## 2. Simple Text Generation

The CLI reads `OPENAI_BASE_URL` and `OPENAI_API_KEY` from your environment (set in the Getting Started section), so it points at Bedrock automatically. The `$MODEL_ID` variable holds the model id you exported there. Use `openai responses create` for a basic prompt:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
openai responses create \
  --model "$MODEL_ID" \
  --input "Explain the difference between Amazon S3 and Amazon EBS in simple terms."
:::

The CLI returns the full JSON response. To extract just the text:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
openai responses create \
  --model "$MODEL_ID" \
  --input "What are the five pillars of the AWS Well-Architected Framework?" \
  --transform 'output.#(type=="message").content.0.text' \
  --raw-output
:::

---

## 3. Using System Instructions

Pass system-level instructions with `instructions` in a YAML body:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
openai responses create \
  --transform 'output.#(type=="message").content.0.text' \
  --raw-output <<YAML
model: $MODEL_ID
instructions: You are a senior Python developer. Provide production-quality code with error handling.
input: Write a function to upload a file to S3 using boto3.
YAML
:::

---

## 4. Controlling Output Parameters

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
openai responses create \
  --model "$MODEL_ID" \
  --input "List 5 AWS services for data analytics." \
  --temperature 0.2 \
  --max-output-tokens 300 \
  --transform 'output.#(type=="message").content.0.text' \
  --raw-output
:::

---

## 5. Piping and Scripting

The CLI reads a YAML request body from standard input, so it composes well with shell pipelines. Here a `cat` heredoc feeds the request in:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat <<YAML | openai responses create \
  --transform 'output.#(type=="message").content.0.text' \
  --raw-output
model: $MODEL_ID
input: What is the OpenAI Responses API?
YAML
:::

Anything that can write a YAML body to stdout (a template engine, a script, another command) can drive the CLI the same way.

---

## 6. Check your work

- ☑ You installed the OpenAI CLI via Homebrew
- ☑ You generated text with `openai responses create`
- ☑ You used `--transform` to extract just the response text
- ☑ You passed a YAML body with system instructions
