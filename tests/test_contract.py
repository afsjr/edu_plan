import pytest

from app.bncc import BaseBNCC
from app.contract import (
    CodigoBNCCInvalido,
    ErroContrato,
    exportar_schema,
    resolver_pacote,
)
from app.exemplo_pacote import pacote_exemplo


@pytest.fixture(scope="module")
def base():
    return BaseBNCC()


@pytest.fixture
def permitidos(base):
    return {habilidade.codigo for habilidade in base.buscar(uso_escolar="Pré II")}


def test_resolve_exemplo(base, permitidos):
    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    assert len(pacote.plano.habilidades) == 7
    assert len(pacote.caderno.atividades) == 5
    assert pacote.avisos == []
    assert pacote.plano.identificacao.codigo_ancora == "EI03EF01"
    assert pacote.plano.habilidades[0].descricao
    assert pacote.caderno.atividades[0].campo_experiencia
    nao_trabalhados = {
        item.codigo for item in pacote.caderno.nota_cobertura.codigos_nao_trabalhados
    }
    assert nao_trabalhados == {"EI03EO01", "EI03EO04"}


def test_atividade_fora_do_plano(base, permitidos):
    gerado = pacote_exemplo()
    gerado.caderno.atividades[0].codigo_bncc = "EI03ET01"
    with pytest.raises(ErroContrato):
        resolver_pacote(gerado, base, permitidos)


def test_rejeita_codigo_fora_da_lista(base, permitidos):
    with pytest.raises(CodigoBNCCInvalido):
        resolver_pacote(pacote_exemplo(), base, {"EI03EF01"})


def test_rejeita_codigo_inexistente(base):
    gerado = pacote_exemplo()
    gerado.plano.habilidades[0].codigo = "EI03XX99"
    with pytest.raises(CodigoBNCCInvalido):
        resolver_pacote(gerado, base, None)


def test_exige_cinco_atividades(base, permitidos):
    gerado = pacote_exemplo()
    gerado.caderno.atividades = gerado.caderno.atividades[:4]
    with pytest.raises(ErroContrato):
        resolver_pacote(gerado, base, permitidos)


def test_exportar_schema(tmp_path):
    destino = exportar_schema(tmp_path / "schema.json")
    assert destino.exists()
    conteudo = destino.read_text(encoding="utf-8")
    assert "PacoteGerado" in conteudo
    assert "codigo_bncc" in conteudo


def test_icones_estranhos_sao_sanitizados(base, permitidos):
    gerado = pacote_exemplo()
    gerado.plano.campos_experiencia[0].icone = "六"
    gerado.plano.recursos[0].icone = "里"
    pacote = resolver_pacote(gerado, base, permitidos)
    assert pacote.plano.campos_experiencia[0].icone == "👥"
    assert pacote.plano.recursos[0].icone == "•"


def test_texto_chines_rejeitado(base, permitidos):
    gerado = pacote_exemplo()
    gerado.plano.campos_experiencia[0].justificativa = "六 欄"
    with pytest.raises(ErroContrato):
        resolver_pacote(gerado, base, permitidos)


def test_objetivo_parafraseado_e_mapeado(base, permitidos):
    gerado = pacote_exemplo()
    gerado.caderno.atividades[0].objetivo_relacionado = (
        "Escrever o próprio nome de forma autônoma."
    )
    pacote = resolver_pacote(gerado, base, permitidos)
    assert pacote.caderno.atividades[0].objetivo_relacionado.startswith(
        "Escrever o próprio nome de forma autônoma"
    )


def test_objetivo_indice_vence_texto(base, permitidos):
    gerado = pacote_exemplo()
    gerado.caderno.atividades[0].objetivo_indice = 2
    gerado.caderno.atividades[0].objetivo_relacionado = "texto errado"
    pacote = resolver_pacote(gerado, base, permitidos)
    assert pacote.caderno.atividades[0].objetivo_relacionado == (
        "Identificar a letra inicial do próprio nome e associá-la ao seu som."
    )


def test_prompt_atividades_sem_descricao_bncc(base, permitidos):
    from app.llm import _prompt_atividades

    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    prompt = _prompt_atividades(pacote.plano)
    assert pacote.plano.habilidades[0].descricao not in prompt
    assert pacote.plano.objetivos[0].itens[0] in prompt
    assert "objetivo_indice" in prompt


def test_mapear_objetivo_parafraseado():
    from app.contract import _mapear_objetivo

    objetivo = (
        "Escrever o próprio nome de forma autônoma, respeitando a ordem das letras."
    )
    assert (
        _mapear_objetivo("Escrever o próprio nome de forma autônoma.", [objetivo])
        == objetivo
    )
