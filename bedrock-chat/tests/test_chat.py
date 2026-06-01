"""Tests for the OpenAI Chat application."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from chat import send_message, stream_message
from config import MODEL, get_client


def test_default_model():
    """Verify the workshop default model is direct OpenAI format."""
    assert MODEL == "gpt-5.5"


@patch("config.OpenAI")
def test_get_client_uses_openai_defaults(mock_openai):
    """Verify get_client does not configure a Bedrock endpoint or bearer token."""
    get_client()
    mock_openai.assert_called_once_with()


def test_send_message():
    """Test that send_message calls the API and returns output text."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "Hello!"

    result = send_message(mock_client, "gpt-5.5", "Hi")

    assert result == "Hello!"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.5",
        input="Hi",
    )


def test_send_message_with_different_model():
    """Test that the model parameter is passed correctly."""
    mock_client = MagicMock()
    mock_client.responses.create.return_value.output_text = "42"

    result = send_message(mock_client, "gpt-5.5", "What is 6*7?")

    assert result == "42"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-5.5",
        input="What is 6*7?",
    )


def test_stream_message(capsys):
    """Test that stream_message prints and returns streamed text."""

    class FakeStream:
        def __iter__(self):
            return iter(
                [
                    SimpleNamespace(type="response.output_text.delta", delta="Hel"),
                    SimpleNamespace(type="response.output_text.delta", delta="lo"),
                    SimpleNamespace(type="response.completed", delta=None),
                ]
            )

        def get_final_response(self):
            return None

    mock_context = MagicMock()
    mock_context.__enter__.return_value = FakeStream()
    mock_context.__exit__.return_value = None

    mock_client = MagicMock()
    mock_client.responses.stream.return_value = mock_context

    result = stream_message(mock_client, "gpt-5.5", "Hi")

    assert result == "Hello"
    assert capsys.readouterr().out == "Hello\n"
    mock_client.responses.stream.assert_called_once_with(
        model="gpt-5.5",
        input="Hi",
    )
