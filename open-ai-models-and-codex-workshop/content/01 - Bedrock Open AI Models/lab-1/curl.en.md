---
title: "(Optional) Access using curl"
weight: 2
---

In this module, you will make direct HTTP requests to the Bedrock-hosted Responses API. The macOS/Linux tabs use `curl`, a command-line tool for transferring data with URLs. The Windows tabs use PowerShell's `Invoke-RestMethod`. Either way, hitting the API directly gives you the most visibility into the raw Responses API request and response format.

**Time:** ~15 minutes 
**Prerequisites:** `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `MODEL_ID` set from Getting Started

---

## 1. Understanding the Endpoint

The Bedrock-hosted Responses API endpoint:

```
POST ${OPENAI_BASE_URL}/responses
```

All requests require:
- **Authorization header**: Bearer token with your Bedrock bearer token (`$OPENAI_API_KEY`)
- **Content-Type header**: `application/json`
- **Request body**: JSON payload in the OpenAI Responses API format

---

## 2. Basic Text Generation

Send a simple prompt to GPT-5.5 and pretty-print the full JSON response:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"Explain what the OpenAI Responses API is in 3 sentences.\"
  }" | jq .
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$headers = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" }
$body = @{
    model = $env:MODEL_ID
    input = "Explain what the OpenAI Responses API is in 3 sentences."
} | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$resp | ConvertTo-Json -Depth 10
:::
::::
:::::

### Understanding the Response

The Responses API returns a structured JSON object:

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1716000000,
  "model": "openai.gpt-5.5",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "The OpenAI Responses API is a modern inference interface..."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 15,
    "output_tokens": 82,
    "total_tokens": 97
  }
}
```

Key fields:
- `output`: array of output items (messages, tool calls, etc.)
- `usage`: token consumption for billing awareness
- `model`: confirms which model served the request

---

## 3. Multi-Turn Conversation

The Responses API is stateful by default. Each response is stored server-side and can be referenced by ID in follow-up requests using `previous_response_id`, so you don't need to resend the full conversation history.

First, send the initial question and capture the response ID:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
RESPONSE_ID=$(curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"What is the capital of France?\",
    \"store\": true
  }" | jq -r '.id')

echo "Response ID: ${RESPONSE_ID}"
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$headers = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" }
$body = @{
    model = $env:MODEL_ID
    input = "What is the capital of France?"
    store = $true
} | ConvertTo-Json
$response1 = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$RESPONSE_ID = $response1.id
Write-Host "Response ID: $RESPONSE_ID"
:::
::::
:::::

Now send a follow-up that references the previous response. The server recalls the full conversation context:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"What is its population?\",
    \"previous_response_id\": \"${RESPONSE_ID}\",
    \"store\": true
  }" | jq .
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$body = @{
    model = $env:MODEL_ID
    input = "What is its population?"
    previous_response_id = $RESPONSE_ID
    store = $true
} | ConvertTo-Json
$response2 = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$response2 | ConvertTo-Json -Depth 10
:::
::::
:::::

:::alert{header="Info" type="info"}
Setting `store: true` persists the response server-side so it can be referenced later. You can also pass the full conversation history manually in the `input` array if you prefer a stateless approach.
:::

---

## 4. System Instructions

Provide system-level instructions to guide the model's behavior:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"instructions\": \"You are a helpful AWS solutions architect. Always provide answers in the context of AWS best practices. Keep responses concise.\",
    \"input\": \"How should I store application secrets?\"
  }" | jq .
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$headers = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" }
$body = @{
    model = $env:MODEL_ID
    instructions = "You are a helpful AWS solutions architect. Always provide answers in the context of AWS best practices. Keep responses concise."
    input = "How should I store application secrets?"
} | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$resp | ConvertTo-Json -Depth 10
:::
::::
:::::

The `instructions` field acts as a system prompt: it sets the model's persona and behavioral constraints without being part of the conversation history.

---

## 5. Streaming Responses

For real-time output, enable streaming with Server-Sent Events:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -N "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"Write a Python function that calculates the Fibonacci sequence using memoization.\",
    \"stream\": true
  }"
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
# Invoke-RestMethod buffers the whole response, so stream with HttpClient instead.
$client = [System.Net.Http.HttpClient]::new()
$req = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Post, "$($env:OPENAI_BASE_URL)/responses")
$req.Headers.Add("Authorization", "Bearer $($env:OPENAI_API_KEY)")
$body = @{
    model = $env:MODEL_ID
    input = "Write a Python function that calculates the Fibonacci sequence using memoization."
    stream = $true
} | ConvertTo-Json
$req.Content = [System.Net.Http.StringContent]::new($body, [System.Text.Encoding]::UTF8, "application/json")
$resp = $client.SendAsync($req, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
$reader = [System.IO.StreamReader]::new($resp.Content.ReadAsStreamAsync().GetAwaiter().GetResult())
while ($null -ne ($line = $reader.ReadLine())) {
    if ($line.StartsWith("data:")) {
        $json = $line.Substring(5).Trim()
        if ($json -and $json -ne "[DONE]") {
            $evt = $json | ConvertFrom-Json
            if ($evt.type -eq "response.output_text.delta") { Write-Host -NoNewline $evt.delta }
        }
    }
}
$reader.Dispose()
Write-Host ""
:::
::::
:::::

The response arrives as a stream of Server-Sent Events (SSE). Each line starts with `data:` followed by a JSON object with a `type` field telling you what happened:

- `response.created`: request accepted, generation starting
- `response.output_text.delta`: a chunk of text (the `delta` field contains the new characters)
- `response.completed`: generation finished, includes final usage stats

:::alert{header="Tip" type="info"}
On macOS/Linux, use `curl -N` (no buffering) to see streaming tokens as they arrive. Without it, curl may buffer the entire response before displaying. On Windows, `Invoke-RestMethod` always buffers, so the example reads the response stream directly with `HttpClient`.
:::

---

## 6. Function Calling (Tool Use)

Define tools that GPT-5.5 can call:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"What is the weather in Seattle?\",
    \"tools\": [
      {
        \"type\": \"function\",
        \"name\": \"get_weather\",
        \"description\": \"Get the current weather for a given location.\",
        \"parameters\": {
          \"type\": \"object\",
          \"properties\": {
            \"location\": {
              \"type\": \"string\",
              \"description\": \"City and state, e.g. Seattle, WA\"
            },
            \"unit\": {
              \"type\": \"string\",
              \"enum\": [\"celsius\", \"fahrenheit\"],
              \"description\": \"Temperature unit\"
            }
          },
          \"required\": [\"location\"]
        }
      }
    ]
  }" | jq .
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$headers = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" }
$body = @{
    model = $env:MODEL_ID
    input = "What is the weather in Seattle?"
    tools = @(
        @{
            type = "function"
            name = "get_weather"
            description = "Get the current weather for a given location."
            parameters = @{
                type = "object"
                properties = @{
                    location = @{ type = "string"; description = "City and state, e.g. Seattle, WA" }
                    unit     = @{ type = "string"; enum = @("celsius", "fahrenheit"); description = "Temperature unit" }
                }
                required = @("location")
            }
        }
    )
} | ConvertTo-Json -Depth 10
$resp = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$resp | ConvertTo-Json -Depth 10
:::
::::
:::::

:::alert{header="Note" type="info"}
In PowerShell, `ConvertTo-Json` only serializes two levels deep by default, which would truncate the nested tool schema. Pass `-Depth 10` so the full `tools` definition is sent.
:::

---

## 7. Configuring Output Parameters

Control response length and format:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
curl -s "${OPENAI_BASE_URL}/responses" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${MODEL_ID}\",
    \"input\": \"List 5 AWS services for data analytics.\",
    \"max_output_tokens\": 500,
    \"temperature\": 0.7
  }" | jq .
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$headers = @{ Authorization = "Bearer $($env:OPENAI_API_KEY)"; "Content-Type" = "application/json" }
$body = @{
    model = $env:MODEL_ID
    input = "List 5 AWS services for data analytics."
    max_output_tokens = 500
    temperature = 0.7
} | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "$($env:OPENAI_BASE_URL)/responses" -Method Post -Headers $headers -Body $body
$resp | ConvertTo-Json -Depth 10
:::
::::
:::::

| Parameter | Description | Default |
|-----------|-------------|---------|
| `max_output_tokens` | Maximum tokens in the response | Model default |
| `temperature` | Randomness (0.0 = deterministic, 2.0 = very random) | 1.0 |
| `top_p` | Nucleus sampling threshold | 1.0 |

---

## 8. Check your work

- ☑ You sent a basic prompt and received a JSON response with `output` and `usage` fields
- ☑ You continued a multi-turn conversation using `previous_response_id`
- ☑ You used streaming and saw tokens arrive incrementally
- ☑ You triggered a function call
