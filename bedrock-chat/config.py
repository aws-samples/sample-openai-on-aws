"""Configuration for the OpenAI Chat application."""

import os

from openai import OpenAI

MODEL = os.environ.get("MODEL_ID", "gpt-5.4")


def get_client() -> OpenAI:
    """Create an OpenAI client using OPENAI_API_KEY from the environment."""
    return OpenAI()
