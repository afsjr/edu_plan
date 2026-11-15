import io
import zipfile

from fastapi.testclient import TestClient

from app import storage
from app.main import app


def _isolar_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "GERACOES", tmp_path / "geracoes")
    monkeypatch.setattr(storage, "BANCO", tmp_path / "historico.db")


def test_modo_demo_devolve_zip(tmp_path, monkeypatch):
    monkeypatch.setenv("VERCEL_DEMO", "1")
    _isolar_storage(tmp_path, monkeypatch)

    cliente = TestClient(app)
    assert cliente.get("/").status_code == 200

    resposta = cliente.post(
        "/gerar",
        data={"uso": "Pré II", "tema": "Meu nome, minha identidade"},
    )
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/zip"
    assert "attachment" in resposta.headers["content-disposition"]

    with zipfile.ZipFile(io.BytesIO(resposta.content)) as arquivo:
        nomes = set(arquivo.namelist())
        assert {"plano_aula.docx", "caderno_atividades.pptx"} <= nomes
        assert arquivo.getinfo("plano_aula.docx").file_size > 10_000
        assert arquivo.getinfo("caderno_atividades.pptx").file_size > 10_000


def test_modo_demo_nao_expoe_historico(tmp_path, monkeypatch):
    monkeypatch.setenv("VERCEL_DEMO", "1")
    _isolar_storage(tmp_path, monkeypatch)

    cliente = TestClient(app)
    assert cliente.get("/historico").status_code == 200
    assert cliente.get("/resultado/qualquer").status_code == 404
    assert cliente.get("/download/qualquer/plano").status_code == 404
