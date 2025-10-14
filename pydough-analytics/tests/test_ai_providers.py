import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import src.pydough_analytics.llm.ai_providers as providers


# ---------------------------
# ClaudeAIProvider
# ---------------------------

def test_claude_ai_provider_stream_parsing(monkeypatch):
    """
    Ensure ClaudeAIProvider.ask concatenates text deltas properly.
    """
    fake_chunk1 = SimpleNamespace(to_dict=lambda: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}})
    fake_chunk2 = SimpleNamespace(to_dict=lambda: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " World"}})

    mock_client = MagicMock()
    mock_client.messages.create.return_value = [fake_chunk1, fake_chunk2]

    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("GOOGLE_PROJECT_ID", "y")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "z")

    monkeypatch.setattr(providers, "AnthropicVertex", lambda project_id, region: SimpleNamespace(messages=mock_client))

    p = providers.ClaudeAIProvider(model_id="claude-3")
    out, usage = p.ask("Q?", "Prompt")
    assert isinstance(out, str)
    assert usage is None


# ---------------------------
# GeminiAIProvider
# ---------------------------

def test_gemini_ai_provider_returns_text(monkeypatch):
    """
    Ensure GeminiAIProvider.ask returns (text, usage_metadata).
    """
    fake_resp = SimpleNamespace(text="Answer", usage_metadata={"tokens": 5})

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = fake_resp

    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("GOOGLE_PROJECT_ID", "y")
    monkeypatch.setenv("GOOGLE_REGION", "z")
    monkeypatch.setattr(providers.genai, "Client", lambda *a, **k: mock_client)

    p = providers.GeminiAIProvider(model_id="gemini-1")
    text, usage = p.ask("Q?", "Prompt")
    assert text == "Answer"
    assert usage == {"tokens": 5}


# ---------------------------
# OtherAIProvider
# ---------------------------

def test_other_ai_provider(monkeypatch):
    """
    Ensure OtherAIProvider.ask delegates to aisuite Client correctly.
    """
    fake_choice = SimpleNamespace(message=SimpleNamespace(content="Other Answer"))
    fake_resp = SimpleNamespace(choices=[fake_choice])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake_resp
    monkeypatch.setattr(providers.ai, "Client", lambda *a, **k: mock_client)

    p = providers.OtherAIProvider("openai", "gpt-4")
    out = p.ask("Q?", "Prompt")
    assert out == "Other Answer"


# ---------------------------
# get_provider
# ---------------------------

@pytest.mark.parametrize(
    "provider,cls_name",
    [
        ("anthropic", providers.ClaudeAIProvider),
        ("google", providers.GeminiAIProvider),
        ("openai", providers.OtherAIProvider),
    ],
)
def test_get_provider_returns_correct_class(monkeypatch, provider, cls_name):
    """
    Ensure get_provider returns the correct class based on provider string.
    """
    monkeypatch.setenv("GOOGLE_PROJECT_ID", "test-proj")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/creds.json")
    monkeypatch.setenv("GOOGLE_API_KEY", "xyz")
    monkeypatch.setattr(providers, "AnthropicVertex", lambda *a, **k: MagicMock())
    monkeypatch.setattr(providers.genai, "Client", lambda *a, **k: MagicMock())
    monkeypatch.setattr(providers.ai, "Client", lambda *a, **k: MagicMock())

    out = providers.get_provider(provider, "model-x")
    assert isinstance(out, cls_name)
