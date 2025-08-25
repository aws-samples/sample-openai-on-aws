#!/usr/bin/env python3
"""
A CLI agent that demonstrates talking to the OpenAI OSS models on Bedrock
"""

import asyncio
import os
import sys

from boto3.session import Config
from strands import Agent
from strands.models import BedrockModel
from strands.telemetry import StrandsTelemetry
from strands_tools import calculator, current_time, file_read, file_write, http_request

# Initialize telemetry
StrandsTelemetry().setup_otlp_exporter()
if os.environ.get("OTEL_CONSOLE"):
    StrandsTelemetry().setup_console_exporter()


async def process_agent_stream(agent: Agent, query: str, show_reasoning: bool = False) -> None:
    """Process agent stream with prefixed output."""
    async for event in agent.stream_async(query):
        if "message" in event and isinstance(event["message"], dict):
            for item in event["message"].get("content", []):
                if "reasoningContent" in item and show_reasoning:
                    text = item["reasoningContent"]["reasoningText"]["text"]
                    print(f"\n🤔 Reasoning:\n{text}\n")
                elif "text" in item and item["text"].strip():
                    print(f"\n💬 Response:\n{item['text']}\n")
                elif "toolUse" in item:
                    print(f"\n🔧 Tool: {item['toolUse']['name']}")
                    print(f"\n🔧 Paramaters:\n{item['toolUse']['input']}\n")
                elif "toolResult" in item:
                    content = item["toolResult"].get("content", [{}])[0].get("text", "")
                    status = item["toolResult"].get("status", "unknown")
                    print(f"\n⚙️ Result ({status}):\n\n{content}\n")

async def interactive_mode(agent: Agent, show_reasoning: bool = False) -> None:
    """Handle interactive mode."""
    print("\n🧬 Strands Agents 🧬 - Interactive Mode\nType 'exit' or 'quit' to end.\n")
    
    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in {"exit", "quit", "/quit", "bye"}:
                print("👋 Goodbye!")
                break
            elif query:
                await process_agent_stream(agent, query, show_reasoning)
                print("\n")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main() -> None:
    """Main entry point."""
    model_id = os.getenv("STRANDS_MODEL_ID", "openai.gpt-oss-20b-1:0")
    max_tokens = int(os.getenv("STRANDS_MAX_TOKENS", "4000"))
    temperature = float(os.getenv("STRANDS_TEMPERATURE", "0.2"))
    streaming = os.getenv("STRANDS_STREAMING", "true").lower() in ("true", "1", "yes")
    show_reasoning = os.getenv("STRANDS_SHOW_REASONING", "true").lower() in ("true", "1", "yes")
    reasoning_effort = os.getenv("STRANDS_REASONING_EFFORT", "low")
    
    print("=" * 60)
    print(f"🤖 Model: {model_id}")
    print(f"🎛️ Max tokens: {max_tokens}, 🌡️ Temperature: {temperature}, 🌊 Streaming: {streaming}")
    print(f"🧠 Show reasoning: {show_reasoning}, 💭 Reasoning effort: {reasoning_effort}")
    print("=" * 60)
    
    agent = Agent(
        model=BedrockModel(
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            streaming=streaming,
            additional_request_fields={"reasoning_effort": reasoning_effort},
            boto_client_config=Config(read_timeout=900, connect_timeout=900, retries={"max_attempts": 3})
        ),
        system_prompt=os.getenv("STRANDS_SYSTEM_PROMPT", 
            "You are a helpful assistant. Reply in rhyme, including Haiku, Syllabic and Alliteration"),
        tools=[current_time, file_read, file_write, http_request, calculator],
        callback_handler=None
    )
    
    if len(sys.argv) > 1:
        asyncio.run(process_agent_stream(agent, " ".join(sys.argv[1:]), show_reasoning))
    else:
        asyncio.run(interactive_mode(agent, show_reasoning))

if __name__ == "__main__":
    main()
