---
title: "Getting Started 🚀"
weight: 1
---

Throughout this workshop you'll invoke OpenAI's GPT models on Amazon Bedrock. You write the same OpenAI SDK and Responses API code you'd use against OpenAI directly. The only differences are that requests are authenticated with either local AWS credentials or an Amazon Bedrock bearer token, pointed at the Bedrock endpoint, and use an `openai.` model-ID prefix.

This page configures the credentials you'll use throughout the workshop, against the workshop model: GPT-5.4 by default, or optionally GPT-5.5 if you prefer. Because Bedrock exposes an OpenAI-compatible endpoint, you'll set all three differences (credentials, endpoint, model ID) as environment variables.

---

## 1. Prerequisites

Make sure you have the following installed on your machine:

- A terminal (macOS Terminal, a Linux shell, or Windows PowerShell)
- Python 3.10+
- `jq` (for JSON formatting in curl exercises): `brew install jq` on macOS, `winget install jqlang.jq` on Windows, or `apt install jq` on Linux
- The [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (used to confirm your identity)

---

## 2. Configure your AWS credentials

This workshop runs in **us-east-2**. You need AWS credentials in your terminal with permission to invoke OpenAI models on Amazon Bedrock.

If your facilitator provided a Workshop Studio account, follow the **Open AWS Console** / **Get AWS CLI credentials** link from your event page and paste the exported credentials into your terminal. Otherwise, use your own configured AWS profile.

Confirm your identity is active:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws sts get-caller-identity
:::

You should see your account ID and assumed role printed back. If you get a credentials error, re-export your workshop credentials before continuing.

---

## 3. Install the Python packages

Install the OpenAI SDK (the primary library we'll use to talk to GPT-5.4) and the Bedrock token generator (which mints the short-lived bearer token from your AWS credentials):

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
pip3 install openai aws-bedrock-token-generator
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
pip install openai aws-bedrock-token-generator
:::
::::
:::::

Verify the SDK installed:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
python3 -c "import openai; print(f'OpenAI SDK version: {openai.__version__}')"
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
python -c "import openai; print(f'OpenAI SDK version: {openai.__version__}')"
:::
::::
:::::

You should see a version number like `2.x.x` printed.

---

## 4. Set your environment variables

Set the region, the Bedrock OpenAI-compatible endpoint, the model ID, and your bearer token. The OpenAI SDK automatically reads `OPENAI_BASE_URL` and `OPENAI_API_KEY`, so once these are set your code stays plain OpenAI code:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
export AWS_REGION="us-east-2"
export OPENAI_BASE_URL="https://bedrock-mantle.${AWS_REGION}.api.aws/openai/v1"
export MODEL_ID="openai.gpt-5.4"
export OPENAI_API_KEY=$(python3 -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='$AWS_REGION'))")
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$env:AWS_REGION = "us-east-2"
$env:OPENAI_BASE_URL = "https://bedrock-mantle.$($env:AWS_REGION).api.aws/openai/v1"
$env:MODEL_ID = "openai.gpt-5.4"
$env:OPENAI_API_KEY = python -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='$($env:AWS_REGION)'))"
:::
::::
:::::

:::alert{type="warning" header="Tokens expire, and variables are session-scoped"}
The bearer token is valid for roughly 12 hours. If requests start failing with a `401`, re-run the `OPENAI_API_KEY` command to mint a fresh one. Environment variables also only last for the current terminal session, so re-run these exports in any new terminal.
:::

:::expand{header="Optional: save your config in a .env file (macOS / Linux)"}
If you'd rather not re-export everything each time you open a new terminal, drop the values into a `.env` file in your working directory:

```bash
cat > .env <<EOF
AWS_REGION=us-east-2
OPENAI_BASE_URL=https://bedrock-mantle.us-east-2.api.aws/openai/v1
MODEL_ID=openai.gpt-5.4
OPENAI_API_KEY=$(python3 -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='us-east-2'))")
EOF
```

Load it into any new shell with:

```bash
set -a && source .env && set +a
```

Remember the bearer token in the file still expires, so regenerate it when it does. Don't commit `.env` to source control.
:::

---

## 5. Verify everything works

Confirm your token and environment are working by making a test request to GPT-5.4 on Bedrock:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"${MODEL_ID}\", \"input\": \"Respond with a fun fact about dinosaurs.\"}" \
  | jq '{status, error, text: ([.output[]? | select(.type=="message") | .content[].text] | join("\n")), usage}'
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$body = @{ model = $env:MODEL_ID; input = "Respond with a fun fact about dinosaurs." } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" } `
  -Body $body
[PSCustomObject]@{
  status = $resp.status
  error  = $resp.error
  text   = ($resp.output | Where-Object { $_.type -eq "message" }).content.text
  usage  = $resp.usage
} | ConvertTo-Json
:::
::::
:::::

A successful call prints `status: "completed"`, `error: null`, the model's `text`, and a `usage` block with token counts. As long as you get a `200` with `status: "completed"` and no `error`, your environment is configured correctly.

That's it, your environment is configured. Proceed to **Part 1** to start working with GPT-5.4 on Amazon Bedrock.

**If something went wrong:**

| Error | Fix |
|-------|-----|
| **401 / authentication error** | Your bearer token likely expired. Re-run the `OPENAI_API_KEY` command in step 4 to mint a fresh one, then try again. |
| **403 / access denied** | Your AWS identity doesn't have access to the OpenAI model on Bedrock. Confirm with `aws sts get-caller-identity` that you're using the workshop credentials. |
| **404 / model not found** | Confirm your `MODEL_ID` is `openai.gpt-5.4` (or `openai.gpt-5.5`). The `openai.` prefix is required on Bedrock, and the model is served from **us-east-2**. |
| **Empty `OPENAI_API_KEY`** | Print the variable to check it. If empty, re-run the export command from step 4. |
| **"command not found: curl"** | Install curl (`brew install curl` on macOS, `apt install curl` on Linux; it ships with Windows). |
| **"command not found: jq"** | Install jq (`brew install jq` on macOS, `apt install jq` on Linux, `winget install jqlang.jq` on Windows). |
