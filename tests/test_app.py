import html
import re

from fastapi.testclient import TestClient

from app.main import app


def _json_do_campo(texto: str, nome: str) -> str:
    casamento = re.search(
        rf'<textarea name="{nome}" hidden>(.*?)</textarea>',
        texto,
        re.S,
    )
    assert casamento is not None, f"campo {nome} não encontrado"
    return html.unescape(casamento.group(1))


def test_fluxo_completo():
    cliente = TestClient(app)

    inicio = cliente.get("/")
    assert inicio.status_code == 200
    assert "Código BNCC" in inicio.text

    plano = cliente.post(
        "/gerar-plano",
        data={"uso": "Pré II", "codigo": "EI03EF01"},
    )
    assert plano.status_code == 200
    assert "Validar plano e gerar atividades" in plano.text
    plano_json = _json_do_campo(plano.text, "plano_json")

    atividades = cliente.post("/gerar-atividades", data={"plano_json": plano_json})
    assert atividades.status_code == 200
    assert "Nota de cobertura" in atividades.text
    caderno_json = _json_do_campo(atividades.text, "caderno_json")

    docx = cliente.post("/baixar-plano", data={"plano_json": plano_json})
    assert docx.status_code == 200
    assert docx.headers["content-type"].endswith("wordprocessingml.document")
    assert len(docx.content) > 10_000

    pptx = cliente.post("/baixar-atividades", data={"caderno_json": caderno_json})
    assert pptx.status_code == 200
    assert pptx.headers["content-type"].endswith("presentationml.presentation")
    assert len(pptx.content) > 10_000


def test_codigo_invalido():
    cliente = TestClient(app)
    resposta = cliente.post(
        "/gerar-plano",
        data={"uso": "Pré II", "codigo": "EI03XX99"},
    )
    assert resposta.status_code == 400
    assert "não possuo esta informação" in resposta.text.lower()


def test_codigo_de_outra_turma():
    cliente = TestClient(app)
    resposta = cliente.post(
        "/gerar-plano",
        data={"uso": "Pré II", "codigo": "EI01EF01"},
    )
    assert resposta.status_code == 400
    assert "não pertence à turma" in resposta.text.lower()
