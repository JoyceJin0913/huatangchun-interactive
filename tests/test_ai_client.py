import pytest
from unittest.mock import patch, MagicMock
from ai_client import call_deepseek


def test_call_deepseek_returns_string(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_key")
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "测试回复内容"

    with patch("ai_client.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        result = call_deepseek(
            system_prompt="你是一个助手",
            user_prompt="你好"
        )

    assert result == "测试回复内容"
    assert isinstance(result, str)


def test_call_deepseek_passes_correct_model(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_key")
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "回复"

    with patch("ai_client.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        call_deepseek(system_prompt="sys", user_prompt="usr")
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "deepseek-chat"
