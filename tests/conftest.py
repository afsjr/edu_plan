import pytest


@pytest.fixture(autouse=True)
def forcar_modo_mock(monkeypatch):
    """Nenhum teste deve chamar OpenAI ou Cloudflare, mesmo com .env preenchido."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
