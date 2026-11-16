from pathlib import Path

from app import storage
from app.llm import MockLLM, RequisicaoGeracao
from app.pipeline import gerar_e_salvar, gerar_pacote


def _requisicao() -> RequisicaoGeracao:
    return RequisicaoGeracao(uso_escolar="Pré II", codigo_ancora="EI03EF01")


def test_gerar_pacote_com_mock():
    pacote = gerar_pacote(_requisicao(), cliente=MockLLM())
    assert len(pacote.plano.habilidades) == 7
    assert len({h.campo_experiencia for h in pacote.plano.habilidades}) == 4
    assert len(pacote.caderno.atividades) == 5
    assert pacote.plano.identificacao.codigo_ancora == "EI03EF01"
    assert any(a.codigo_bncc == "EI03EF01" for a in pacote.caderno.atividades)
    assert pacote.avisos == []


def test_gerar_pacote_outro_codigo():
    requisicao = RequisicaoGeracao(uso_escolar="Pré II", codigo_ancora="EI03ET07")
    pacote = gerar_pacote(requisicao, cliente=MockLLM())
    assert len(pacote.plano.habilidades) == 7
    assert len(pacote.caderno.atividades) == 5
    assert pacote.plano.identificacao.codigo_ancora == "EI03ET07"
    assert any(a.codigo_bncc == "EI03ET07" for a in pacote.caderno.atividades)


def test_gerar_e_salvar(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE", tmp_path)
    monkeypatch.setattr(storage, "GERACOES", tmp_path / "geracoes")
    monkeypatch.setattr(storage, "BANCO", tmp_path / "historico.db")

    resultado = gerar_e_salvar(_requisicao(), cliente=MockLLM())

    plano = Path(resultado["caminho_plano"])
    caderno = Path(resultado["caminho_caderno"])
    assert plano.exists() and plano.suffix == ".docx"
    assert caderno.exists() and caderno.suffix == ".pptx"
    assert (plano.parent / "pacote.json").exists()

    registro = storage.obter(resultado["id"])
    assert registro is not None
    assert len(registro["codigos"]) == 7
    assert registro["tema"] == resultado["pacote"].plano.identificacao.tema
