"""Tests for the Bedrock Chat application."""

from unittest.mock import MagicMock, patch

from chat import send_message
from config import REGION, BASE_URL, MODEL


def test_config_structure():
    """Verify configuration values have expected structure."""
    assert "bedrock-mantle" in BASE_URL
    assert "openai/v1" in BASE_URL
    assert MODEL.startswith("openai.")
    assert len(REGION) > 0


def test_send_message():
    """Test that send_message calls the API and returns output text."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "Hello!"

    result = send_message(mock_client, "openai.gpt-5.4", "Hi")

    assert result == "Hello!"
    mock_client.responses.create.assert_called_once_with(
        model="openai.gpt-5.4",
        input="Hi",
    )


def test_send_message_with_different_model():
    """Test that the model parameter is passed correctly."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "42"

    result = send_message(mock_client, "openai.gpt-oss-120b", "What is 6*7?")

    assert result == "42"
    mock_client.responses.create.assert_called_once_with(
        model="openai.gpt-oss-120b",
        input="What is 6*7?",
    )
