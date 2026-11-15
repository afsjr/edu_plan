from pathlib import Path

from app import storage
from app.llm import MockLLM, RequisicaoGeracao
from app.pipeline import gerar_e_salvar, gerar_pacote


def _requisicao() -> RequisicaoGeracao:
    return RequisicaoGeracao(uso_escolar="Pré II", tema="Meu nome, minha identidade")


def test_gerar_pacote_com_mock():
    pacote = gerar_pacote(_requisicao(), cliente=MockLLM())
    assert len(pacote.caderno.atividades) == 5
    assert len(pacote.plano.habilidades) >= 4
    assert all(habilidade.codigo.startswith("EI03") for habilidade in pacote.plano.habilidades)
    assert pacote.avisos == []


def test_gerar_pacote_generico():
    requisicao = RequisicaoGeracao(uso_escolar="Pré II", tema="Animais do jardim")
    pacote = gerar_pacote(requisicao, cliente=MockLLM())
    assert len(pacote.caderno.atividades) == 5
    assert len(pacote.plano.campos_experiencia) == 4
    assert len(pacote.plano.habilidades) == 7
    assert all(habilidade.codigo.startswith("EI03") for habilidade in pacote.plano.habilidades)


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
    assert registro["tema"] == "Meu nome, minha identidade"
    assert len(registro["codigos"]) >= 4
