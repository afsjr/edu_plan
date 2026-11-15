import os

from app.config import carregar_env


def test_carregar_env(tmp_path, monkeypatch):
    arquivo = tmp_path / ".env"
    arquivo.write_text("# comentário\nPLANO_AULA_TESTE=ok\n", encoding="utf-8")
    monkeypatch.delenv("PLANO_AULA_TESTE", raising=False)

    carregar_env(arquivo)

    assert os.environ["PLANO_AULA_TESTE"] == "ok"
