# OpenAI Chat

A simple CLI chat application powered by GPT-5.4 through the OpenAI API.

## What this does

This is a basic synchronous chat loop. It sends your messages to GPT-5.4 using the OpenAI Python SDK and prints the responses.

## What's intentionally missing (your exercise)

This app is deliberately minimal. During the workshop, you'll use Codex to add:

- **Streaming support** — See responses appear token-by-token
- **Conversation history** — Multi-turn context so the model remembers earlier messages
- **Structured output mode** — Get responses in JSON format with a defined schema

## Setup

```bash
pip install -r requirements.txt
```

Set your OpenAI API key before running the app:

```bash
export OPENAI_API_KEY="paste-your-api-key-here"
export MODEL_ID="gpt-5.4"
```

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
python chat.py --model gpt-5.4
```

## Project structure

```
bedrock-chat/
├── chat.py           # Main application (CLI entry point)
├── config.py         # OpenAI client configuration
├── requirements.txt  # Python dependencies
├── tests/
│   └── test_chat.py  # Unit tests
└── README.md         # This file
```
