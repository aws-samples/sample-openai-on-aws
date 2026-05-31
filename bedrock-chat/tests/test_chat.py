"""Tests for the OpenAI Chat application."""

from unittest.mock import MagicMock, patch

from chat import send_message
from config import MODEL, get_client


def test_default_model():
    """Verify the workshop default model is direct OpenAI format."""
    assert MODEL == "gpt-5.4"


@patch("config.OpenAI")
def test_get_client_uses_openai_defaults(mock_openai):
    """Verify get_client does not configure a Bedrock endpoint or bearer token."""
    get_client()
    mock_openai.assert_called_once_with()


def test_send_message():
    """Test that send_message calls the API and returns output text."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "Hello!"

    result = send_message(mock_client, "gpt-5.4", "Hi")

    assert result == "Hello!"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.4",
        input="Hi",
    )


def test_send_message_with_different_model():
    """Test that the model parameter is passed correctly."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "42"

    result = send_message(mock_client, "gpt-5.4", "What is 6*7?")

    assert result == "42"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.4",
        input="What is 6*7?",
    )
