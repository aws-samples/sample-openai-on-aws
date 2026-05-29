# Bedrock Chat

A simple CLI chat application powered by GPT-5.4 on Amazon Bedrock Mantle.

## What this does

This is a basic synchronous chat loop. It sends your messages to GPT-5.4 via the Amazon Bedrock Mantle endpoint and prints the responses.

## What's intentionally missing (your exercise)

This app is deliberately minimal. During the workshop, you'll use Codex to add:

- **Streaming support** — See responses appear token-by-token
- **Conversation history** — Multi-turn context so the model remembers earlier messages
- **Structured output mode** — Get responses in JSON format with a defined schema

## Setup

```bash
pip install -r requirements.txt
```

Ensure your AWS credentials are configured and you have access to OpenAI models on Bedrock.

## Usage

```bash
# Interactive chat
python chat.py

# Single message (for testing)
python chat.py --single "What is 2+2?"

# Stream tokens as they arrive
python chat.py --stream

# Stream a single response
python chat.py --stream --single "Tell me a haiku about clouds"

# Use a different model
python chat.py --model openai.gpt-oss-120b
```

## Project structure

```
bedrock-chat/
├── chat.py           # Main application (CLI entry point)
├── config.py         # Bedrock endpoint and client configuration
├── requirements.txt  # Python dependencies
├── tests/
│   └── test_chat.py  # Unit tests
└── README.md         # This file
```
