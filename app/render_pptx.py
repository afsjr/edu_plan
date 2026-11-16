"""Renderiza o caderno de atividades em .pptx A4 editável.

As atividades são desenhadas com formas, textos e tabelas nativas do
PowerPoint. Nada é uma imagem achatada: o professor pode mover, trocar texto
e corrigir o material.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Cm, Pt

from app.contract import Atividade, CadernoAtividades, ConteudoAtividade, ItemLegendaCor
from app.icons import icone_para

VERDE = "4CAF73"
LARANJA = "F2683C"
AZUL = "2D9CDB"
ROXO = "9B6DD6"
ROSA = "F45B9C"
AMARELO = "FDC22D"
AZUL_ESCURO = "1B6CA8"
CINZA_CLARO = "F4F5F8"
CINZA_TEXTO = "6E6E80"
CINZA_ESCURO = "2E2E3A"
CINZA_LINHA = "C9C9D2"
BRANCO = "FFFFFF"

FONTE = "Arial"

LARGURA = 21.01
ALTURA = 29.69
MARGEM = 1.8
CONTEUDO = LARGURA - 2 * MARGEM

CORES_ATIVIDADES = [AZUL, LARANJA, VERDE, ROXO, ROSA, AMARELO]
CORES_LEGENDA = ["F45B9C", "FDC22D", "2D9CDB", "4CAF73", "F2683C", "9B6DD6"]


def _rgb(hexadecimal: str) -> RGBColor:
    return RGBColor.from_string(hexadecimal)


def _texto(
    slide,
    x: float,
    y: float,
    largura: float,
    altura: float,
    texto: str,
    tamanho: float = 12,
    negrito: bool = False,
    cor: str = CINZA_ESCURO,
    alinhamento=PP_ALIGN.LEFT,
    ancoragem=MSO_ANCHOR.TOP,
    espacamento: float = 1.05,
    italico: bool = False,
):
    caixa = slide.shapes.add_textbox(Cm(x), Cm(y), Cm(largura), Cm(altura))
    quadro = caixa.text_frame
    quadro.word_wrap = True
    quadro.vertical_anchor = ancoragem
    quadro.margin_left = 0
    quadro.margin_right = 0
    quadro.margin_top = 0
    quadro.margin_bottom = 0

    linhas = str(texto).split("\n")
    for indice, linha in enumerate(linhas):
        paragrafo = quadro.paragraphs[0] if indice == 0 else quadro.add_paragraph()
        paragrafo.alignment = alinhamento
        paragrafo.line_spacing = espacamento
        executar = paragrafo.add_run()
        executar.text = linha
        executar.font.name = FONTE
        executar.font.size = Pt(tamanho)
        executar.font.bold = negrito
        executar.font.italic = italico
        executar.font.color.rgb = _rgb(cor)
    return caixa


def _forma(
    slide,
    x: float,
    y: float,
    largura: float,
    altura: float,
    preenchimento: str | None = None,
    contorno: str | None = None,
    espessura: float = 1.5,
    arredondado: bool = True,
    forma=MSO_SHAPE.ROUNDED_RECTANGLE,
):
    shape = slide.shapes.add_shape(forma, Cm(x), Cm(y), Cm(largura), Cm(altura))
    shape.shadow.inherit = False
    if preenchimento:
        shape.fill.solid()
        shape.fill.fore_color.rgb = _rgb(preenchimento)
    else:
        shape.fill.background()
    if contorno:
        shape.line.color.rgb = _rgb(contorno)
        shape.line.width = Pt(espessura)
    else:
        shape.line.fill.background()
    if arredondado and forma == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shape.adjustments[0] = 0.12
        except Exception:
            pass
    return shape


def _texto_na_forma(
    shape,
    texto: str,
    tamanho: float = 12,
    negrito: bool = False,
    cor: str = CINZA_ESCURO,
    alinhamento=PP_ALIGN.CENTER,
    ancoragem=MSO_ANCHOR.MIDDLE,
    margem: float = 0.12,
):
    quadro = shape.text_frame
    quadro.word_wrap = True
    quadro.vertical_anchor = ancoragem
    quadro.margin_left = Cm(margem)
    quadro.margin_right = Cm(margem)
    quadro.margin_top = Cm(margem)
    quadro.margin_bottom = Cm(margem)

    linhas = str(texto).split("\n")
    for indice, linha in enumerate(linhas):
        paragrafo = quadro.paragraphs[0] if indice == 0 else quadro.add_paragraph()
        paragrafo.alignment = alinhamento
        executar = paragrafo.add_run()
        executar.text = linha
        executar.font.name = FONTE
        executar.font.size = Pt(tamanho)
        executar.font.bold = negrito
        executar.font.color.rgb = _rgb(cor)


def _linha(slide, x1: float, y1: float, x2: float, y2: float, cor: str = CINZA_LINHA, espessura: float = 1.25, tracejada: bool = False):
    conector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Cm(x1), Cm(y1), Cm(x2), Cm(y2))
    conector.line.color.rgb = _rgb(cor)
    conector.line.width = Pt(espessura)
    if tracejada:
        conector.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return conector


def _circulo(slide, x: float, y: float, diametro: float, preenchimento: str, contorno: str | None = None, espessura: float = 1.5):
    return _forma(
        slide,
        x,
        y,
        diametro,
        diametro,
        preenchimento=preenchimento,
        contorno=contorno,
        espessura=espessura,
        arredondado=False,
        forma=MSO_SHAPE.OVAL,
    )


def _rodape(slide, caderno: CadernoAtividades, numero: int) -> None:
    _linha(slide, MARGEM, 27.7, LARGURA - MARGEM, 27.7, CINZA_LINHA, 0.75)
    _texto(
        slide,
        MARGEM,
        28.0,
        CONTEUDO - 3.0,
        1.0,
        f"Atividade {numero}  •  {caderno.capa.titulo}  •  {caderno.capa.etapa}",
        tamanho=8,
        cor=CINZA_TEXTO,
    )
    _texto(
        slide,
        LARGURA - MARGEM - 2.5,
        28.0,
        2.5,
        1.0,
        f"{numero + 1}",
        tamanho=8,
        cor=CINZA_TEXTO,
        alinhamento=PP_ALIGN.RIGHT,
    )


def _cabecalho_atividade(slide, atividade: Atividade, cor: str) -> None:
    _forma(slide, 0, 0, LARGURA, 2.9, preenchimento=cor, arredondado=False, forma=MSO_SHAPE.RECTANGLE)
    _circulo(slide, MARGEM, 0.65, 1.55, BRANCO)
    _texto(
        slide,
        MARGEM,
        0.65,
        1.55,
        1.55,
        str(atividade.numero),
        tamanho=20,
        negrito=True,
        cor=cor,
        alinhamento=PP_ALIGN.CENTER,
        ancoragem=MSO_ANCHOR.MIDDLE,
    )
    _texto(
        slide,
        MARGEM + 2.1,
        0.55,
        8.8,
        1.8,
        atividade.titulo,
        tamanho=18,
        negrito=True,
        cor=BRANCO,
        ancoragem=MSO_ANCHOR.MIDDLE,
    )

    selo = _forma(slide, LARGURA - MARGEM - 6.0, 0.72, 6.0, 1.5, preenchimento=BRANCO, arredondado=True)
    _texto_na_forma(selo, f"{atividade.codigo_bncc}  •  {atividade.campo_experiencia}", tamanho=7.8, negrito=True, cor=cor)

    tem_imagem = bool(atividade.imagem_base64)
    largura_texto = CONTEUDO - 0.7
    if tem_imagem:
        largura_texto -= 2.5

    _forma(slide, MARGEM, 3.35, CONTEUDO, 2.35, preenchimento=CINZA_CLARO, arredondado=True)
    _texto(
        slide,
        MARGEM + 0.35,
        3.5,
        largura_texto,
        1.15,
        atividade.enunciado,
        tamanho=10 if tem_imagem else 11,
        cor=CINZA_ESCURO,
        ancoragem=MSO_ANCHOR.MIDDLE,
    )
    _texto(
        slide,
        MARGEM + 0.35,
        4.7,
        largura_texto,
        0.8,
        f"Objetivo: {atividade.objetivo_relacionado}",
        tamanho=7.5,
        cor=CINZA_TEXTO,
        ancoragem=MSO_ANCHOR.MIDDLE,
    )

    if tem_imagem:
        try:
            dados = base64.b64decode(atividade.imagem_base64)
            slide.shapes.add_picture(
                io.BytesIO(dados),
                Cm(MARGEM + 0.35 + largura_texto + 0.2),
                Cm(3.45),
                width=Cm(2.1),
                height=Cm(2.1),
            )
        except Exception:
            pass


def _conteudo_cobrir_palavra(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    _texto(slide, MARGEM, 6.2, CONTEUDO, 1.0, "Cubra as letrinhas pontilhadas:", tamanho=11, negrito=True, cor=cor)
    palavra = (conteudo.texto_para_cobrir or "TEMA").upper()
    caixa = _forma(slide, MARGEM, 7.4, CONTEUDO, 4.2, preenchimento=BRANCO, contorno=cor, arredondado=True)
    _texto_na_forma(caixa, " ".join(palavra), tamanho=40, negrito=True, cor=CINZA_LINHA)

    _texto(slide, MARGEM, 12.4, CONTEUDO, 1.0, "Agora escreva a palavra:", tamanho=11, negrito=True, cor=cor)
    for indice in range(max(2, conteudo.linhas_escrita or 2)):
        y = 14.0 + indice * 2.2
        _linha(slide, MARGEM + 1.0, y, LARGURA - MARGEM - 1.0, y, CINZA_LINHA, 1.0, tracejada=True)

    escreva = _forma(slide, MARGEM + 4.0, 21.2, CONTEUDO - 8.0, 4.6, preenchimento="FFF8E0", contorno=AMARELO, arredondado=True)
    _texto_na_forma(escreva, "escreva aqui", tamanho=11, negrito=True, cor=LARANJA)


def _conteudo_desenhar(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Desenhe aqui:", tamanho=11, negrito=True, cor=cor)
    quadro = _forma(slide, MARGEM + 2.0, 7.2, CONTEUDO - 4.0, 10.5, preenchimento="FFFDF5", contorno=cor, espessura=2.0, arredondado=True)
    _texto_na_forma(quadro, "desenhe aqui", tamanho=12, cor=CINZA_LINHA)

    frases = conteudo.frases or ["O que eu mais gosto:", "Minha cor favorita é:"]
    largura_caixa = (CONTEUDO - 0.6) / 2
    for indice, frase in enumerate(frases[:4]):
        coluna = indice % 2
        linha = indice // 2
        x = MARGEM + coluna * (largura_caixa + 0.6)
        y = 18.2 + linha * 2.5
        caixa = _forma(slide, x, y, largura_caixa, 2.0, preenchimento=CINZA_CLARO, contorno=cor, arredondado=True)
        _texto_na_forma(caixa, frase, tamanho=9.5, negrito=False, cor=CINZA_ESCURO)


def _conteudo_ligar(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Ligue cada desenho à letra com que o nome começa:", tamanho=11, negrito=True, cor=cor)
    pares = conteudo.pares or []
    if not pares:
        _texto(slide, MARGEM, 8.0, CONTEUDO, 2.0, "Sem pares informados.", tamanho=11, cor=CINZA_TEXTO)
        return

    limite = min(len(pares), 5)
    passo = 3.0 if limite > 3 else 3.6
    inicio_y = 8.0
    for indice, par in enumerate(pares[:limite]):
        y = inicio_y + indice * passo
        cartao = _forma(slide, MARGEM + 0.4, y, 7.2, 2.2, preenchimento=BRANCO, contorno=cor, espessura=1.5, arredondado=True)
        icone = icone_para(par.palavra)
        texto = f"{icone}  {par.palavra}" if icone else par.palavra
        _texto_na_forma(cartao, texto, tamanho=13, negrito=True, cor=CINZA_ESCURO)
        _circulo(slide, MARGEM + 7.9, y + 0.25, 0.55, cor)

        letra = _circulo(slide, LARGURA - MARGEM - 3.4, y + 0.15, 2.0, "FFF8E0", contorno=cor, espessura=1.8)
        _texto_na_forma(letra, par.letra.upper(), tamanho=18, negrito=True, cor=cor)

    _texto(slide, MARGEM, 24.8, CONTEUDO, 1.4, "Dica: use o dedinho ou o lápis para traçar o caminho.", tamanho=9, italico=True, cor=CINZA_TEXTO)


def _conteudo_colorir(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Pinte cada espaço seguindo a cor de cada número:", tamanho=11, negrito=True, cor=cor)
    legenda = conteudo.legenda_cores or []
    numeros = [item.numero for item in legenda] or [1, 2, 3, 4]

    colunas, linhas = 5, 4
    tamanho = 3.0
    espaco = 0.28
    inicio_x = MARGEM + 0.5
    inicio_y = 7.6
    for indice in range(colunas * linhas):
        coluna = indice % colunas
        linha = indice // colunas
        x = inicio_x + coluna * (tamanho + espaco)
        y = inicio_y + linha * (tamanho + espaco)
        numero = numeros[indice % len(numeros)]
        celula = _forma(slide, x, y, tamanho, tamanho, preenchimento=BRANCO, contorno=cor, espessura=1.25, arredondado=True)
        _texto_na_forma(celula, str(numero), tamanho=16, negrito=True, cor=cor)

    y_legenda = inicio_y + linhas * (tamanho + espaco) + 1.2
    _texto(slide, MARGEM, y_legenda, CONTEUDO, 0.8, "Legenda", tamanho=10, negrito=True, cor=cor)
    itens = legenda or [
        ItemLegendaCor(numero=i + 1, cor=nome)
        for i, nome in enumerate(["Rosa", "Amarelo", "Azul", "Verde"])
    ]
    largura_item = CONTEUDO / max(len(itens), 1)
    for indice, item in enumerate(itens):
        x = MARGEM + indice * largura_item
        y = y_legenda + 1.0
        _circulo(slide, x, y, 1.0, CORES_LEGENDA[indice % len(CORES_LEGENDA)], contorno=CINZA_LINHA, espessura=0.75)
        _texto(slide, x - 0.2, y + 1.3, largura_item - 0.2, 1.2, f"{item.numero} = {item.cor}", tamanho=8, cor=CINZA_ESCURO)


def _conteudo_labirinto(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Ajude a criança a chegar na escola seguindo o caminho:", tamanho=11, negrito=True, cor=cor)

    inicio = conteudo.rotulo_inicio or "início"
    fim = conteudo.rotulo_fim or "escola"

    casa = _forma(slide, MARGEM + 1.0, 7.6, 4.0, 3.2, preenchimento="FFF8E0", contorno=cor, espessura=1.75, arredondado=True)
    _texto_na_forma(casa, f"🏠\n{inicio}", tamanho=10, negrito=True, cor=LARANJA)

    escola = _forma(slide, LARGURA - MARGEM - 5.0, 20.6, 4.0, 3.2, preenchimento="EAF6FF", contorno=AZUL, espessura=1.75, arredondado=True)
    _texto_na_forma(escola, f"🏫\n{fim}", tamanho=10, negrito=True, cor=AZUL_ESCURO)

    pontos = [
        (MARGEM + 5.8, 8.2),
        (MARGEM + 9.8, 10.6),
        (MARGEM + 5.8, 13.0),
        (MARGEM + 9.8, 15.4),
        (MARGEM + 5.8, 17.8),
    ]
    for indice, (x, y) in enumerate(pontos):
        pedra = _circulo(slide, x, y, 1.6, CORES_ATIVIDADES[indice % len(CORES_ATIVIDADES)])
        _texto_na_forma(pedra, "", tamanho=8)

    _linha(slide, MARGEM + 4.8, 9.0, MARGEM + 5.8, 9.0, CINZA_LINHA, 1.0, tracejada=True)
    _linha(slide, MARGEM + 7.2, 9.0, MARGEM + 9.8, 11.2, CINZA_LINHA, 1.0, tracejada=True)
    _linha(slide, MARGEM + 10.6, 11.2, MARGEM + 7.2, 13.6, CINZA_LINHA, 1.0, tracejada=True)
    _linha(slide, MARGEM + 7.2, 13.6, MARGEM + 9.8, 16.0, CINZA_LINHA, 1.0, tracejada=True)
    _linha(slide, MARGEM + 10.6, 16.0, MARGEM + 7.2, 18.4, CINZA_LINHA, 1.0, tracejada=True)
    _linha(slide, MARGEM + 7.2, 18.4, LARGURA - MARGEM - 5.0, 21.8, CINZA_LINHA, 1.0, tracejada=True)

    _texto(slide, MARGEM, 24.8, CONTEUDO, 1.4, "Trace o caminho com o dedo e depois com o lápis.", tamanho=9, italico=True, cor=CINZA_TEXTO)


def _conteudo_generico(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    caixa = _forma(slide, MARGEM, 6.2, CONTEUDO, 19.0, preenchimento=BRANCO, contorno=cor, arredondado=True)
    frases = conteudo.frases + conteudo.elementos_extras
    _texto_na_forma(
        caixa,
        "\n".join(frases) if frases else "Espaço para a atividade.",
        tamanho=12,
        cor=CINZA_ESCURO,
        alinhamento=PP_ALIGN.LEFT,
        ancoragem=MSO_ANCHOR.TOP,
        margem=0.6,
    )


def _conteudo_contar(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    quantidade = max(1, min(conteudo.quantidade or 5, 20))
    icone = icone_para(conteudo.icone_chave or "bola")
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Conte os objetos e escreva o número:", tamanho=11, negrito=True, cor=cor)

    colunas = 5
    tamanho = 2.4
    espaco = 0.28
    inicio_x = MARGEM + 1.3
    inicio_y = 7.6
    for indice in range(quantidade):
        coluna = indice % colunas
        linha = indice // colunas
        x = inicio_x + coluna * (tamanho + espaco)
        y = inicio_y + linha * (tamanho + espaco)
        celula = _forma(slide, x, y, tamanho, tamanho, preenchimento=BRANCO, contorno=cor, espessura=1.0, arredondado=True)
        _texto_na_forma(celula, icone, tamanho=22, cor=CINZA_ESCURO)

    linhas = (quantidade + colunas - 1) // colunas
    y_resposta = inicio_y + linhas * (tamanho + espaco) + 1.0
    _texto(slide, MARGEM, y_resposta, 6.0, 1.0, "Resposta:", tamanho=11, negrito=True, cor=cor)
    _forma(slide, MARGEM + 3.2, y_resposta - 0.1, 3.4, 1.7, preenchimento=BRANCO, contorno=cor, espessura=1.6, arredondado=True)
    _texto(slide, MARGEM, 24.8, CONTEUDO, 1.4, "Conte devagar, tocando cada objeto.", tamanho=9, italico=True, cor=CINZA_TEXTO)


def _conteudo_completar(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    sequencia = (conteudo.sequencia or ["1", "2", "3", "4", "5"])[:8]
    lacunas = max(1, min(conteudo.lacunas or 1, len(sequencia)))
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Complete a sequência:", tamanho=11, negrito=True, cor=cor)

    total = len(sequencia)
    largura = min(2.8, (CONTEUDO - 0.6) / max(total, 1) - 0.3)
    x0 = MARGEM + 0.5
    y = 8.5
    for indice, item in enumerate(sequencia):
        vazio = indice >= total - lacunas
        caixa = _forma(
            slide,
            x0 + indice * (largura + 0.3),
            y,
            largura,
            2.6,
            preenchimento="FFF8E0" if vazio else BRANCO,
            contorno=cor,
            espessura=1.5,
            arredondado=True,
        )
        _texto_na_forma(
            caixa,
            "?" if vazio else item,
            tamanho=18,
            negrito=True,
            cor=cor if vazio else CINZA_ESCURO,
        )

    _texto(slide, MARGEM, 12.6, CONTEUDO, 1.2, "Escreva os itens que faltam:", tamanho=11, negrito=True, cor=cor)
    for indice in range(lacunas):
        _linha(
            slide,
            MARGEM + 1.0 + indice * 4.0,
            15.0,
            MARGEM + 4.2 + indice * 4.0,
            15.0,
            CINZA_LINHA,
            1.0,
            tracejada=True,
        )


def _conteudo_recortar_colar(slide, conteudo: ConteudoAtividade, cor: str) -> None:
    itens = (conteudo.itens_recortar or ["círculo", "quadrado", "triângulo"])[:4]
    _texto(slide, MARGEM, 6.0, CONTEUDO, 1.0, "Recorte as formas e cole no lugar certo:", tamanho=11, negrito=True, cor=cor)

    for indice, item in enumerate(itens):
        forma = _forma(
            slide,
            MARGEM + indice * 4.0,
            7.6,
            3.2,
            3.0,
            preenchimento=BRANCO,
            contorno=cor,
            espessura=1.6,
            arredondado=True,
        )
        forma.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        _texto_na_forma(forma, item, tamanho=11, negrito=True, cor=CINZA_ESCURO)

    alvo = _forma(slide, MARGEM, 13.0, CONTEUDO, 10.0, preenchimento="FFFDF5", contorno=cor, espessura=1.2, arredondado=True)
    _texto_na_forma(alvo, "cole aqui", tamanho=12, cor=CINZA_LINHA)


CONTEUDOS = {
    "cobrir_palavra": _conteudo_cobrir_palavra,
    "ligar": _conteudo_ligar,
    "contar": _conteudo_contar,
    "colorir": _conteudo_colorir,
    "completar": _conteudo_completar,
    "desenhar": _conteudo_desenhar,
    "labirinto": _conteudo_labirinto,
    "recortar_colar": _conteudo_recortar_colar,
}


def _capa(prs: Presentation, caderno: CadernoAtividades) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    _forma(slide, 0, 0, LARGURA, 9.6, preenchimento=AZUL, arredondado=False, forma=MSO_SHAPE.RECTANGLE)
    _circulo(slide, LARGURA - 5.4, -2.4, 6.0, "4FA8DE")
    _circulo(slide, LARGURA - 3.2, 5.0, 2.4, LARANJA)
    _circulo(slide, LARGURA - 2.6, 7.9, 1.3, AMARELO)

    _texto(slide, MARGEM, 1.5, CONTEUDO, 1.0, "CADERNO DE ATIVIDADES", tamanho=11, negrito=True, cor=BRANCO)
    _texto(slide, MARGEM, 3.0, CONTEUDO - 2.0, 3.4, caderno.capa.titulo, tamanho=30, negrito=True, cor=BRANCO)
    _texto(slide, MARGEM, 6.8, CONTEUDO - 2.0, 1.2, caderno.capa.subtitulo, tamanho=13, cor=BRANCO)

    _forma(slide, MARGEM, 11.0, CONTEUDO, 2.0, preenchimento=CINZA_CLARO, arredondado=True)
    _texto(slide, MARGEM + 0.4, 11.25, CONTEUDO - 0.8, 1.5, f"{caderno.capa.etapa}  •  {caderno.capa.faixa_etaria}  •  {caderno.capa.codigo_ancora}", tamanho=12, negrito=True, cor=CINZA_ESCURO)

    selo = _forma(slide, MARGEM, 13.6, 8.2, 1.6, preenchimento="FFF8E0", contorno=AMARELO, arredondado=True)
    _texto_na_forma(selo, caderno.capa.alinhamento_bncc, tamanho=10, negrito=True, cor=LARANJA)

    icones = ["✏️", "🔤", "🎨", "🔢", "🧩"]
    for indice, icone in enumerate(icones):
        x = MARGEM + indice * 3.5
        y = 18.0
        circulo = _circulo(slide, x, y, 2.8, CORES_ATIVIDADES[indice % len(CORES_ATIVIDADES)])
        _texto_na_forma(circulo, icone, tamanho=20, negrito=False, cor=BRANCO)

    _texto(slide, MARGEM, 23.0, CONTEUDO, 1.0, f"{len(caderno.atividades)} atividades para imprimir em A4", tamanho=12, negrito=True, cor=AZUL_ESCURO)
    _texto(slide, MARGEM, 24.4, CONTEUDO, 1.6, "Material de apoio ao plano de aula. Revisar antes de aplicar.", tamanho=9, italico=True, cor=CINZA_TEXTO)

    _linha(slide, MARGEM, 27.7, LARGURA - MARGEM, 27.7, CINZA_LINHA, 0.75)
    _texto(slide, MARGEM, 28.0, CONTEUDO, 1.0, caderno.capa.titulo, tamanho=8, cor=CINZA_TEXTO)


def _slide_nota(prs: Presentation, caderno: CadernoAtividades) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _forma(slide, 0, 0, LARGURA, 2.9, preenchimento=CINZA_ESCURO, arredondado=False, forma=MSO_SHAPE.RECTANGLE)
    _texto(slide, MARGEM, 0.7, CONTEUDO, 1.8, "Nota para o professor", tamanho=20, negrito=True, cor=BRANCO, ancoragem=MSO_ANCHOR.MIDDLE)
    _texto(slide, MARGEM, 3.4, CONTEUDO, 1.0, "Cobertura do plano", tamanho=14, negrito=True, cor=AZUL_ESCURO)

    nota = caderno.nota_cobertura
    y = 4.6
    if nota.codigos_nao_trabalhados:
        _texto(slide, MARGEM, y, CONTEUDO, 1.0, "Habilidades do plano não trabalhadas nas atividades:", tamanho=10.5, negrito=True, cor=LARANJA)
        y += 1.1
        for item in nota.codigos_nao_trabalhados:
            _texto(slide, MARGEM, y, CONTEUDO, 1.2, f"{item.codigo} — {item.descricao}", tamanho=9, cor=CINZA_ESCURO)
            y += 1.4
    if nota.objetivos_nao_trabalhados:
        _texto(slide, MARGEM, y, CONTEUDO, 1.0, "Objetivos não contemplados:", tamanho=10.5, negrito=True, cor=LARANJA)
        y += 1.1
        for objetivo in nota.objetivos_nao_trabalhados:
            _texto(slide, MARGEM, y, CONTEUDO, 1.0, f"• {objetivo}", tamanho=9, cor=CINZA_ESCURO)
            y += 1.1
    if nota.sugestoes_extras:
        _texto(slide, MARGEM, y, CONTEUDO, 1.0, "Sugestões extras:", tamanho=10.5, negrito=True, cor=VERDE)
        y += 1.1
        for sugestao in nota.sugestoes_extras:
            _texto(slide, MARGEM, y, CONTEUDO, 1.0, f"• {sugestao}", tamanho=9, cor=CINZA_ESCURO)
            y += 1.1
    if not (nota.codigos_nao_trabalhados or nota.objetivos_nao_trabalhados or nota.sugestoes_extras):
        _texto(slide, MARGEM, 5.0, CONTEUDO, 2.0, "Todas as habilidades e objetivos do plano foram trabalhados nas atividades.", tamanho=11, cor=CINZA_ESCURO)

    _texto(slide, MARGEM, 25.5, CONTEUDO, 1.4, "Este slide é opcional: o professor pode removê-lo antes de imprimir.", tamanho=8.5, italico=True, cor=CINZA_TEXTO)
    _linha(slide, MARGEM, 27.7, LARGURA - MARGEM, 27.7, CINZA_LINHA, 0.75)
    _texto(slide, MARGEM, 28.0, CONTEUDO - 3.0, 1.0, f"Nota de cobertura  •  {caderno.capa.titulo}  •  {caderno.capa.etapa}", tamanho=8, cor=CINZA_TEXTO)
    _texto(slide, LARGURA - MARGEM - 2.5, 28.0, 2.5, 1.0, str(len(caderno.atividades) + 2), tamanho=8, cor=CINZA_TEXTO, alinhamento=PP_ALIGN.RIGHT)


def render_caderno(caderno: CadernoAtividades, destino: Path) -> Path:
    prs = Presentation()
    prs.slide_width = Cm(LARGURA)
    prs.slide_height = Cm(ALTURA)

    _capa(prs, caderno)

    for indice, atividade in enumerate(caderno.atividades):
        cor = CORES_ATIVIDADES[indice % len(CORES_ATIVIDADES)]
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _cabecalho_atividade(slide, atividade, cor)
        renderizador = CONTEUDOS.get(atividade.tipo, _conteudo_generico)
        renderizador(slide, atividade.conteudo, cor)
        _rodape(slide, caderno, atividade.numero)

    _slide_nota(prs, caderno)

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    prs.save(destino)
    return destino


if __name__ == "__main__":
    from app.exemplo_pacote import pacote_exemplo
    from app.bncc import BaseBNCC
    from app.contract import resolver_pacote

    base = BaseBNCC()
    permitidos = {h.codigo for h in base.buscar(uso_escolar="Pré II")}
    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    saida = render_caderno(pacote.caderno, Path("storage/exemplo_caderno.pptx"))
    print(f"Gerado: {saida}")
