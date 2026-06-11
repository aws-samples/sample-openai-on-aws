---
title: "Part 1: 🧠 OpenAI Frontier Models"
weight: 9
---

## 1. What is GPT-5.5?

**OpenAI GPT-5.5** is the default model used for this workshop. You access both models through the **OpenAI Responses API**, a modern, tool-capable inference interface that supports text, image input, structured output, function calling, streaming, and multi-turn state when you choose to use it.

Key capabilities:

- **Advanced reasoning** — strong performance on complex tasks
- **Tool use** — native support for function calling and MCP tools
- **Large context window** — process extensive inputs for comprehensive analysis
- **Multi-modal support** — text and image understanding

## 2. What is the OpenAI Responses API?

The **Responses API** is OpenAI's modern inference API for model responses and agentic workflows. Individual requests can be used independently, but the API also supports stateful patterns through stored responses, `previous_response_id`, and Conversations. Key features:

- **Conversation state** — continue a thread with `previous_response_id`, use Conversations, or pass full history yourself for a stateless pattern
- **Function calling** — native support for tool use with structured arguments
- **Items-based format** — uses `input` items and returns `output` items (not messages/choices)
- **Streaming support** — real-time token streaming via Server-Sent Events
- **Reasoning control** — adjustable reasoning effort (low/medium/high)
- **Structured output** — JSON object format for predictable responses
- **Image input** — multimodal support via base64-encoded images

:::alert{type="info" header="Responses API mental model"}
Think of a response as an ordered set of **items** rather than a single chat message. Your input can include text, images, previous assistant messages, and tool results. The model output can include text, reasoning-related items, function calls, MCP tool calls, and structured JSON. Your application decides which items to keep, which tools to execute, and whether to continue the thread with `previous_response_id` or by passing history manually.
:::

| Capability | What it lets you build | Where you'll see it |
|------------|------------------------|---------------------|
| **State** | Multi-turn applications without manually resending every message | Lab 1 |
| **Structured outputs** | JSON and typed objects for pipelines and APIs | Lab 1 |
| **Function calling** | Model-selected calls into your own code or services | Lab 2 |
| **Parallel tool calls** | Multiple independent tool calls in one model turn | Lab 2 |
| **Vision** | Image understanding for dashboards, documents, and diagrams | Lab 3 |
| **Agents SDK** | Higher-level orchestration around model calls and tools | Lab 4 |

## 3. Workshop Flow

| Lab | What you'll do |
|-----|---------------|
| **Lab 1: Access OpenAI Models** | Use the OpenAI SDK to invoke GPT-5.5 or GPT-5.4, manage state, and return structured output. Optionally explore curl and the CLI. |
| **Lab 2: Function Calling** | Define tools, trigger function calls, and handle parallel tool calls |
| **Lab 3: Vision** | Analyze images with multimodal model capabilities |
| **Lab 4: Agents SDK** | Orchestrate multi-step agent workflows with tool execution |
