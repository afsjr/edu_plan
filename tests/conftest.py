import pytest


@pytest.fixture(autouse=True)
def forcar_modo_mock(monkeypatch):
    """Nenhum teste deve chamar um provedor real, mesmo com .env preenchido."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
