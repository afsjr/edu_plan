import pytest

from app.bncc_ef import BaseBNCCEF, CodigoNaoEncontrado


@pytest.fixture(scope="module")
def base():
    return BaseBNCCEF()


def test_resumo_da_base_ef(base):
    resumo = base.resumo()
    assert resumo["total"] == 574
    assert resumo["por_ciclo"] == {
        "01": 79,
        "02": 89,
        "03": 94,
        "04": 95,
        "05": 95,
        "12": 31,
        "15": 45,
        "35": 46,
    }
    assert resumo["por_componente"] == {
        "AR": 26,
        "CI": 48,
        "EF": 27,
        "ER": 33,
        "GE": 56,
        "HI": 52,
        "LP": 206,
        "MA": 126,
    }


def test_por_codigo_traz_texto_oficial(base):
    habilidade = base.por_codigo("EF01LP01")
    assert habilidade is not None
    assert habilidade.habilidade.startswith("Reconhecer que textos")
    assert habilidade.componente == "Língua Portuguesa"
    assert habilidade.anos == {1}


def test_codigo_multi_ano_cobre_intervalo(base):
    arte = base.por_codigo("EF15AR01")
    assert arte is not None
    assert arte.anos == {1, 2, 3, 4, 5}

    ef_12 = base.por_codigo("EF12EF01")
    assert ef_12 is not None
    assert ef_12.anos == {1, 2}

    ef_35 = base.por_codigo("EF35EF01")
    assert ef_35 is not None
    assert ef_35.anos == {3, 4, 5}


def test_busca_filtra_ano_e_componente(base):
    resultados = base.buscar(ano=1, componente="LP")
    assert resultados
    assert all(1 in habilidade.anos for habilidade in resultados)
    assert all(habilidade.sigla_componente == "LP" for habilidade in resultados)


def test_componentes_disponiveis_no_primeiro_ano(base):
    componentes = base.componentes_disponiveis(1)
    assert len(componentes) == 8
    assert ("LP", "Língua Portuguesa") in componentes
    assert ("AR", "Arte") in componentes


def test_seleciona_ancora_e_relacionados_ef(base):
    selecionados = base.selecionar_codigos("EF01LP01", 1)
    assert len(selecionados) == 7
    assert selecionados[0].codigo == "EF01LP01"
    assert len({habilidade.sigla_componente for habilidade in selecionados}) == 4
    assert all(1 in habilidade.anos for habilidade in selecionados)


def test_ancora_inexistente_ef(base):
    with pytest.raises(CodigoNaoEncontrado):
        base.selecionar_codigos("EF01XX99", 1)


def test_ancora_de_outro_ano_ef(base):
    with pytest.raises(CodigoNaoEncontrado):
        base.selecionar_codigos("EF12EF01", 3)


def test_pagina_html_do_fundamental_i():
    from fastapi.testclient import TestClient

    from app.main import app

    cliente = TestClient(app)
    resposta = cliente.get("/bncc-ef")
    assert resposta.status_code == 200
    assert "574" in resposta.text
    assert "EF01LP01" in resposta.text

    filtrada = cliente.get("/bncc-ef?ano=1&componente=LP")
    assert filtrada.status_code == 200
    assert "EF01LP01" in filtrada.text


def test_pipeline_fund1_com_mock():
    from app.llm import MockLLM, RequisicaoGeracao
    from app.pipeline import gerar_pacote

    requisicao = RequisicaoGeracao(uso_escolar="1º ano", codigo_ancora="EF01LP01")
    pacote = gerar_pacote(requisicao, cliente=MockLLM())

    assert len(pacote.plano.habilidades) == 7
    assert len({h.campo_experiencia for h in pacote.plano.habilidades}) == 4
    assert len(pacote.plano.objetivos) == 1
    assert pacote.plano.objetivos[0].ano == "1º ano"
    assert len(pacote.caderno.atividades) == 5
    assert pacote.plano.identificacao.codigo_ancora == "EF01LP01"
    assert any(a.codigo_bncc == "EF01LP01" for a in pacote.caderno.atividades)
    assert pacote.avisos == []


def test_render_fund1_docx_e_pptx(tmp_path):
    from docx import Document
    from pptx import Presentation

    from app.llm import MockLLM, RequisicaoGeracao
    from app.pipeline import gerar_pacote
    from app.render_docx import render_plano
    from app.render_pptx import render_caderno

    requisicao = RequisicaoGeracao(uso_escolar="1º ano", codigo_ancora="EF01LP01")
    pacote = gerar_pacote(requisicao, cliente=MockLLM())

    docx = render_plano(pacote.plano, tmp_path / "plano_ef.docx")
    documento = Document(docx)
    texto = "\n".join(
        [paragrafo.text for paragrafo in documento.paragraphs]
        + [
            celula.text
            for tabela in documento.tables
            for linha in tabela.rows
            for celula in linha.cells
        ]
    )
    assert "Componentes curriculares" in texto
    assert "Inicial" in texto
    assert "Esperado" in texto
    assert "Pré I" not in texto
    assert "Campos de experiência" not in texto

    pptx = render_caderno(pacote.caderno, tmp_path / "caderno_ef.pptx")
    apresentacao = Presentation(pptx)
    assert len(apresentacao.slides) == 6
    capa = " ".join(
        shape.text
        for shape in apresentacao.slides[0].shapes
        if shape.has_text_frame
    )
    assert "Ensino Fundamental" in capa
    assert "6 a 7 anos" in capa


def test_fluxo_html_fund1():
    import html
    import re

    from fastapi.testclient import TestClient

    from app.main import app

    cliente = TestClient(app)
    inicio = cliente.get("/fund1")
    assert inicio.status_code == 200
    assert "EF01LP01" in inicio.text

    plano = cliente.post(
        "/gerar-plano-fund1",
        data={"ano": "1º ano", "codigo": "EF01LP01"},
    )
    assert plano.status_code == 200
    assert "Componentes curriculares" in plano.text
    casamento = re.search(
        r'<textarea name="plano_json" hidden>(.*?)</textarea>',
        plano.text,
        re.S,
    )
    assert casamento is not None
    plano_json = html.unescape(casamento.group(1))

    atividades = cliente.post("/gerar-atividades", data={"plano_json": plano_json})
    assert atividades.status_code == 200
    assert "Nota de cobertura" in atividades.text
