from fastapi.testclient import TestClient

from app import storage
from app.main import app


def test_fluxo_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "GERACOES", tmp_path / "geracoes")
    monkeypatch.setattr(storage, "BANCO", tmp_path / "historico.db")

    cliente = TestClient(app)

    assert cliente.get("/").status_code == 200
    assert cliente.get("/bncc").status_code == 200
    assert cliente.get("/historico").status_code == 200
    assert cliente.get("/saude").json()["base"]["total"] == 93

    resposta = cliente.post(
        "/gerar",
        data={"uso": "Pré II", "tema": "Meu nome, minha identidade"},
        follow_redirects=False,
    )
    assert resposta.status_code == 303

    local = resposta.headers["location"]
    assert local.startswith("/resultado/")
    geracao_id = local.rsplit("/", 1)[-1]

    resultado = cliente.get(local)
    assert resultado.status_code == 200
    assert "Baixar plano" in resultado.text
    assert "Baixar caderno" in resultado.text

    plano = cliente.get(f"/download/{geracao_id}/plano")
    assert plano.status_code == 200
    assert plano.headers["content-type"].endswith("wordprocessingml.document")
    assert len(plano.content) > 10_000

    caderno = cliente.get(f"/download/{geracao_id}/caderno")
    assert caderno.status_code == 200
    assert caderno.headers["content-type"].endswith("presentationml.presentation")
    assert len(caderno.content) > 10_000

    filtro = cliente.get("/bncc", params={"grupo": "EI03", "campo": "EF", "texto": "escrita"})
    assert filtro.status_code == 200
    assert "EI03EF01" in filtro.text


def test_tema_vazio_e_rejeitado(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "GERACOES", tmp_path / "geracoes")
    monkeypatch.setattr(storage, "BANCO", tmp_path / "historico.db")

    cliente = TestClient(app)
    resposta = cliente.post(
        "/gerar",
        data={"uso": "Pré II", "tema": "   "},
        follow_redirects=False,
    )
    assert resposta.status_code == 400
    assert "Descreva o tema" in resposta.text
