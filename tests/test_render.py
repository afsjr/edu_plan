from docx import Document
from pptx import Presentation

from app.bncc import BaseBNCC
from app.contract import resolver_pacote
from app.exemplo_pacote import pacote_exemplo
from app.render_docx import render_plano
from app.render_pptx import render_caderno


def _pacote_resolvido():
    base = BaseBNCC()
    permitidos = {habilidade.codigo for habilidade in base.buscar(grupo="EI03")}
    return resolver_pacote(pacote_exemplo(), base, permitidos)


def _texto_docx(documento: Document) -> str:
    partes = [paragrafo.text for paragrafo in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                partes.append(celula.text)
    return "\n".join(partes)


def test_render_plano_docx(tmp_path):
    pacote = _pacote_resolvido()
    caminho = render_plano(pacote.plano, tmp_path / "plano.docx")

    assert caminho.exists()
    assert caminho.stat().st_size > 10_000

    documento = Document(caminho)
    texto = _texto_docx(documento)

    for termo in [
        "PLANO DE AULA",
        "Identificação",
        "Campos de experiência",
        "Objetivos de aprendizagem",
        "Habilidades da BNCC",
        "Recursos e materiais",
        "Desenvolvimento da aula",
        "Brincadeira & atividade para casa",
        "Avaliação",
        "Adaptações e acessibilidade",
        "Observações do(a) professor(a)",
        "EI03EF01",
        "Expressar ideias",
    ]:
        assert termo in texto

    for proibido in ["六", "里", "💡", "😊", "✔"]:
        assert proibido not in texto
    assert "Sigla" in texto

    assert len(documento.tables) >= 15


def test_render_caderno_pptx(tmp_path):
    pacote = _pacote_resolvido()
    caminho = render_caderno(pacote.caderno, tmp_path / "caderno.pptx")

    assert caminho.exists()
    assert caminho.stat().st_size > 10_000

    apresentacao = Presentation(caminho)
    assert len(apresentacao.slides) == 7
    assert round(apresentacao.slide_width / 360000, 1) == 21.0
    assert round(apresentacao.slide_height / 360000, 1) == 29.7

    textos = [
        " ".join(
            shape.text_frame.text
            for shape in slide.shapes
            if shape.has_text_frame
        )
        for slide in apresentacao.slides
    ]

    assert "CADERNO DE ATIVIDADES" in textos[0]
    assert "Este é o meu nome!" in textos[1]
    assert "🍍" in textos[3] and "ABACAXI" in textos[3]
    assert "O caminho até a escola" in textos[5]
    assert "Nota para o professor" in textos[6]
    assert "EI03EO01" in textos[6] or "EI03EO04" in textos[6]


PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="


def test_render_caderno_com_imagem(tmp_path):
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    pacote = _pacote_resolvido()
    atividades = [
        a.model_copy(update={"imagem_base64": PNG_1X1}) if a.numero == 1 else a
        for a in pacote.caderno.atividades
    ]
    caderno = pacote.caderno.model_copy(update={"atividades": atividades})
    caminho = render_caderno(caderno, tmp_path / "caderno_img.pptx")

    apresentacao = Presentation(caminho)
    fotos = [
        shape
        for shape in apresentacao.slides[1].shapes
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE
    ]
    assert fotos
