"""Configuration for the Bedrock Chat application."""

import os

from openai import OpenAI
from aws_bedrock_token_generator import provide_token

REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-west-2"))
BASE_URL = f"https://bedrock-mantle.{REGION}.api.aws/openai/v1"
MODEL = os.environ.get("MODEL_ID", "openai.gpt-5.4")


def get_client() -> OpenAI:
    """Create an OpenAI client configured for Amazon Bedrock Mantle."""
    token = provide_token(region=REGION)
    return OpenAI(api_key=token, base_url=BASE_URL)
