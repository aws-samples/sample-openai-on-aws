#!/usr/bin/env python3
"""OpenAI Chat — A simple CLI chat application powered by GPT-5.4.

This is a basic synchronous chat loop. It sends user messages to the model
and prints responses. There is no streaming, no conversation history, and
no structured output — those are features you will add during the workshop.
"""

import argparse
import sys

from config import get_client, MODEL


def send_message(client, model: str, message: str) -> str:
    """Send a single message to the model and return the response text."""
    response = client.responses.create(
        model=model,
        input=message,
    )
    return response.output_text


def stream_message(client, model: str, message: str) -> str:
    """Send a single message and stream the response text as it arrives."""
    chunks = []

    with client.responses.stream(
        model=model,
        input=message,
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                delta = event.delta
                chunks.append(delta)
                print(delta, end="", flush=True)

        stream.get_final_response()

    print()
    return "".join(chunks)


def main():
    parser = argparse.ArgumentParser(description="Chat with GPT-5.4 using the OpenAI API")
    parser.add_argument("--model", default=MODEL, help="Model ID to use")
    parser.add_argument("--single", type=str, help="Send a single message and exit")
    parser.add_argument("--stream", action="store_true", help="Stream tokens as they arrive")
    args = parser.parse_args()

    client = get_client()

    # Single message mode (for scripting/testing)
    if args.single:
        if args.stream:
            stream_message(client, args.model, args.single)
        else:
            response = send_message(client, args.model, args.single)
            print(response)
        return

    # Interactive chat loop
    print(f"OpenAI Chat (model: {args.model})")
    print("Type your message and press Enter. Type 'quit' to exit.")
    print("-" * 40)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        try:
            if args.stream:
                print("\nAssistant: ", end="", flush=True)
                stream_message(client, args.model, user_input)
            else:
                response = send_message(client, args.model, user_input)
                print(f"\nAssistant: {response}")
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
