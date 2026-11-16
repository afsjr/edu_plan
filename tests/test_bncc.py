import pytest

from app.bncc import BaseBNCC


@pytest.fixture(scope="module")
def base():
    return BaseBNCC()


def test_resumo_da_base(base):
    resumo = base.resumo()
    assert resumo["total"] == 93
    assert resumo["por_grupo"] == {"EI01": 29, "EI02": 32, "EI03": 32}
    assert resumo["por_campo"] == {"CG": 15, "EF": 27, "EO": 20, "ET": 22, "TS": 9}


def test_pre_ii_usa_codigos_ei03(base):
    resultados = base.buscar(uso_escolar="Pré II")
    assert len(resultados) == 32
    assert {habilidade.codigo[:4] for habilidade in resultados} == {"EI03"}


def test_busca_respeita_palavra_inteira(base):
    resultados = base.buscar(texto="nome")
    codigos = {habilidade.codigo for habilidade in resultados}
    assert "EI01EF01" in codigos
    assert "EI02ET02" not in codigos  # "fenômenos" não deve casar com "nome"


def test_filtro_por_campo(base):
    resultados = base.buscar(campo="Escuta, fala, pensamento e imaginação")
    assert len(resultados) == 27
    assert all(habilidade.sigla_campo == "EF" for habilidade in resultados)


def test_por_codigo_traz_texto_oficial(base):
    habilidade = base.por_codigo("EI03EF01")
    assert habilidade is not None
    assert habilidade.objetivo.startswith("Expressar ideias")
    assert habilidade.grupo_etario == "Crianças pequenas"


def test_grupo_invalido_falha(base):
    with pytest.raises(ValueError):
        base.buscar(grupo="Pré III")


def test_seleciona_ancora_e_relacionados(base):
    selecionados = base.selecionar_codigos("EI03EF01", "Pré II")
    assert len(selecionados) == 7
    assert selecionados[0].codigo == "EI03EF01"
    assert len({h.sigla_campo for h in selecionados}) == 4
    assert all(h.codigo.startswith("EI03") for h in selecionados)
    assert all(base.por_codigo(h.codigo) is not None for h in selecionados)


def test_ancora_inexistente(base):
    from app.bncc import CodigoNaoEncontrado

    with pytest.raises(CodigoNaoEncontrado):
        base.selecionar_codigos("EI03XX99", "Pré II")


def test_ancora_de_outra_turma(base):
    from app.bncc import CodigoNaoEncontrado

    with pytest.raises(CodigoNaoEncontrado):
        base.selecionar_codigos("EI01EF01", "Pré II")
