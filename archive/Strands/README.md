# GPT-OSS CLI Agent

A CLI agent that demonstrates talking to the OpenAI OSS models on Amazon Bedrock using the Strands Agents framework.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode
Run without arguments to enter interactive mode:
```bash
python gpt-oss-cli.py
```

### Single Query Mode
Pass your query as command line arguments:
```bash
python gpt-oss-cli.py "What is the weather like today?"
```

## Configuration

Configure the agent using environment variables:

### Model Configuration
- `STRANDS_MODEL_ID` - Model to use (default: `openai.gpt-oss-120b-1:0`)
  - Available models: `openai.gpt-oss-120b-1:0`, `openai.gpt-oss-20b-1:0`

### Generation Parameters
- `STRANDS_MAX_TOKENS` - Maximum tokens to generate (default: `1000`)
- `STRANDS_TEMPERATURE` - Temperature for randomness (default: `0.2`)
- `STRANDS_STREAMING` - Enable streaming responses (default: `false`)

### Reasoning Configuration
- `STRANDS_SHOW_REASONING` - Show model reasoning process (default: `false`)
- `STRANDS_REASONING_EFFORT` - Reasoning level (default: `low`)
  - Available levels: `low`, `medium`, `high`

### System Prompt
- `STRANDS_SYSTEM_PROMPT` - Custom system prompt (default: rhyming assistant)

## Examples

```bash
# Use the 20B model with high reasoning
export STRANDS_MODEL_ID="openai.gpt-oss-20b-1:0"
export STRANDS_REASONING_EFFORT="high"
export STRANDS_SHOW_REASONING="true"
python gpt-oss-cli.py

# Single query with custom temperature
export STRANDS_TEMPERATURE="0.7"
python gpt-oss-cli.py "Write a creative story about AI"
```

## Available Tools

The agent has access to these tools:
- `current_time` - Get current date and time
- `file_read` - Read files from the filesystem
- `file_write` - Write files to the filesystem
- `http_request` - Make HTTP requests
- `calculator` - Perform calculations
