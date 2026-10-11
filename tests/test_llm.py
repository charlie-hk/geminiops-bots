import pytest

from core.llm import GeminiClient, GeminiNotConfigured


def test_raises_clear_error_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = GeminiClient()
    with pytest.raises(GeminiNotConfigured):
        client.generate("hello")
