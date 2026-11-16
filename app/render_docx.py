"""Renderiza o plano de aula em .docx editável, no formato A4.

O documento é montado com python-docx a partir do contrato `PlanoAula`.
Texto continua texto, tabela continua tabela e cores continuam editáveis —
nada é achatado em imagem, porque o professor vai corrigir o material.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.contract import ObjetivosAno, PlanoAula

# Paleta do modelo
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
CORES_MOMENTOS = [ROSA, LARANJA, AMARELO, VERDE, ROXO, AZUL, VERDE, LARANJA]

LARGURA_UTIL = 17.2  # cm, com margens de 1,9 cm em A4 (21 cm)


def _rgb(hexadecimal: str) -> RGBColor:
    return RGBColor.from_string(hexadecimal)


def _sombra_celula(celula, cor: str) -> None:
    tc_pr = celula._tc.get_or_add_tcPr()
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:color"), "auto")
    sombra.set(qn("w:fill"), cor)
    tc_pr.append(sombra)


def _margens_celula(celula, topo: int = 70, baixo: int = 70, esquerda: int = 110, direita: int = 110) -> None:
    tc_pr = celula._tc.get_or_add_tcPr()
    margens = OxmlElement("w:tcMar")
    for nome, valor in (("top", topo), ("left", esquerda), ("bottom", baixo), ("right", direita)):
        elemento = OxmlElement(f"w:{nome}")
        elemento.set(qn("w:w"), str(valor))
        elemento.set(qn("w:type"), "dxa")
        margens.append(elemento)
    tc_pr.append(margens)


def _bordas_tabela(tabela, cor: str = "D9D9D9", tamanho: int = 4) -> None:
    tabela_pr = tabela._tbl.tblPr
    bordas = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:val"), "single")
        elemento.set(qn("w:sz"), str(tamanho))
        elemento.set(qn("w:space"), "0")
        elemento.set(qn("w:color"), cor)
        bordas.append(elemento)
    tabela_pr.append(bordas)


def _sem_bordas(tabela) -> None:
    tabela_pr = tabela._tbl.tblPr
    bordas = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:val"), "none")
        elemento.set(qn("w:sz"), "0")
        elemento.set(qn("w:space"), "0")
        elemento.set(qn("w:color"), "auto")
        bordas.append(elemento)
    tabela_pr.append(bordas)


def _texto_celula(
    celula,
    texto: str,
    tamanho: float = 9,
    negrito: bool = False,
    cor: str = CINZA_ESCURO,
    alinhamento=WD_ALIGN_PARAGRAPH.LEFT,
) -> None:
    celula.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    paragrafo = celula.paragraphs[0]
    paragrafo.alignment = alinhamento
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.space_before = Pt(0)

    for indice, linha in enumerate(str(texto).split("\n")):
        if indice > 0:
            paragrafo = celula.add_paragraph()
            paragrafo.alignment = alinhamento
            paragrafo.paragraph_format.space_after = Pt(0)
        executar = paragrafo.add_run(linha)
        executar.font.name = FONTE
        executar.font.size = Pt(tamanho)
        executar.font.bold = negrito
        executar.font.color.rgb = _rgb(cor)


def _paragrafo_texto(
    doc,
    texto: str,
    tamanho: float = 9,
    cor: str = CINZA_ESCURO,
    italico: bool = False,
):
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(3)
    executar = paragrafo.add_run(texto)
    executar.font.name = FONTE
    executar.font.size = Pt(tamanho)
    executar.font.italic = italico
    executar.font.color.rgb = _rgb(cor)
    return paragrafo


def _larguras(tabela, larguras_cm: list[float]) -> None:
    tabela.autofit = False
    tabela.allow_autofit = False
    for indice, largura in enumerate(larguras_cm):
        for linha in tabela.rows:
            linha.cells[indice].width = Cm(largura)
        tabela.columns[indice].width = Cm(largura)


def _nova_tabela(doc, linhas: int, colunas: int, larguras_cm: list[float]):
    tabela = doc.add_table(rows=linhas, cols=colunas)
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    _larguras(tabela, larguras_cm)
    return tabela


def _secao(doc, numero: str, titulo: str, subtitulo: str, cor: str = AZUL) -> None:
    tabela = _nova_tabela(doc, 1, 2, [1.35, LARGURA_UTIL - 1.35])
    _sem_bordas(tabela)

    esquerda, direita = tabela.rows[0].cells
    _sombra_celula(esquerda, cor)
    _margens_celula(esquerda, topo=90, baixo=90)
    _texto_celula(esquerda, numero, tamanho=17, negrito=True, cor=BRANCO, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)

    _sombra_celula(direita, CINZA_CLARO)
    _margens_celula(direita, topo=90, baixo=90)
    paragrafo = direita.paragraphs[0]
    paragrafo.paragraph_format.space_after = Pt(0)
    executar = paragrafo.add_run(titulo)
    executar.font.name = FONTE
    executar.font.size = Pt(13)
    executar.font.bold = True
    executar.font.color.rgb = _rgb(AZUL_ESCURO)

    if subtitulo:
        paragrafo_sub = direita.add_paragraph()
        paragrafo_sub.paragraph_format.space_after = Pt(0)
        executar_sub = paragrafo_sub.add_run(subtitulo)
        executar_sub.font.name = FONTE
        executar_sub.font.size = Pt(8.5)
        executar_sub.font.color.rgb = _rgb(CINZA_TEXTO)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _cabecalho_tabela(tabela, titulos: list[str], cor: str) -> None:
    for indice, titulo in enumerate(titulos):
        celula = tabela.rows[0].cells[indice]
        _sombra_celula(celula, cor)
        _margens_celula(celula)
        _texto_celula(celula, titulo, tamanho=8.5, negrito=True, cor=BRANCO)


def _tabela_dados(doc, titulos: list[str], linhas: list[list[str]], larguras_cm: list[float], cor: str) -> None:
    tabela = _nova_tabela(doc, len(linhas) + 1, len(titulos), larguras_cm)
    _bordas_tabela(tabela, cor="E4E4EA")
    _cabecalho_tabela(tabela, titulos, cor)

    for indice_linha, valores in enumerate(linhas, start=1):
        for indice_coluna, valor in enumerate(valores):
            celula = tabela.rows[indice_linha].cells[indice_coluna]
            _margens_celula(celula)
            _sombra_celula(celula, BRANCO if indice_linha % 2 else CINZA_CLARO)
            _texto_celula(celula, valor, tamanho=9)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _tabela_identificacao(doc, plano: PlanoAula) -> None:
    identificacao = plano.identificacao
    pares = [
        ("Tema da aula", identificacao.tema),
        ("Turmas", " e ".join(identificacao.turmas)),
        ("Tempo estimado", identificacao.tempo_estimado),
        ("Área integradora", identificacao.area_integradora),
        ("Data", "____ / ____ / ________"),
        ("Professor(a)", "__________________________________________"),
    ]

    tabela = _nova_tabela(doc, len(pares), 2, [4.6, LARGURA_UTIL - 4.6])
    _bordas_tabela(tabela, cor="E4E4EA")

    for indice, (rotulo, valor) in enumerate(pares):
        celula_rotulo, celula_valor = tabela.rows[indice].cells
        _sombra_celula(celula_rotulo, CINZA_CLARO)
        _margens_celula(celula_rotulo)
        _texto_celula(celula_rotulo, rotulo, tamanho=9, negrito=True, cor=AZUL_ESCURO)

        _sombra_celula(celula_valor, BRANCO)
        _margens_celula(celula_valor)
        _texto_celula(celula_valor, valor, tamanho=9)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _bloco_objetivos(doc, objetivos: ObjetivosAno, cor: str) -> None:
    tabela = _nova_tabela(doc, 1, 2, [3.2, LARGURA_UTIL - 3.2])
    _sem_bordas(tabela)

    rotulo, conteudo = tabela.rows[0].cells
    _sombra_celula(rotulo, cor)
    _margens_celula(rotulo)
    _texto_celula(rotulo, objetivos.ano, tamanho=9, negrito=True, cor=BRANCO)

    _sombra_celula(conteudo, CINZA_CLARO)
    _margens_celula(conteudo)
    for indice, item in enumerate(objetivos.itens):
        paragrafo = conteudo.paragraphs[0] if indice == 0 else conteudo.add_paragraph()
        paragrafo.paragraph_format.space_after = Pt(1)
        executar = paragrafo.add_run(f"• {item}")
        executar.font.name = FONTE
        executar.font.size = Pt(9)
        executar.font.color.rgb = _rgb(CINZA_ESCURO)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _caixa_dica(doc, dica: str) -> None:
    tabela = _nova_tabela(doc, 1, 1, [LARGURA_UTIL])
    _sem_bordas(tabela)
    celula = tabela.rows[0].cells[0]
    _sombra_celula(celula, "FFF8E0")
    _margens_celula(celula, topo=110, baixo=110, esquerda=160, direita=160)
    _texto_celula(celula, f"💡  Dica: {dica}", tamanho=9, cor=LARANJA)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _caixa_brincadeira(doc, plano: PlanoAula) -> None:
    brincadeira = plano.brincadeira_casa
    tabela = _nova_tabela(doc, 2, 1, [LARGURA_UTIL])
    _sem_bordas(tabela)

    titulo = tabela.rows[0].cells[0]
    _sombra_celula(titulo, LARANJA)
    _margens_celula(titulo, topo=100, baixo=100, esquerda=160, direita=160)
    _texto_celula(titulo, f"😊  Brincadeira: {brincadeira.titulo}", tamanho=10.5, negrito=True, cor=BRANCO)

    corpo = tabela.rows[1].cells[0]
    _sombra_celula(corpo, "FFF6F2")
    _margens_celula(corpo, topo=110, baixo=110, esquerda=160, direita=160)
    paragrafo = corpo.paragraphs[0]
    paragrafo.paragraph_format.space_after = Pt(3)
    executar = paragrafo.add_run(brincadeira.descricao)
    executar.font.name = FONTE
    executar.font.size = Pt(9)
    executar.font.color.rgb = _rgb(CINZA_ESCURO)

    if brincadeira.organizacao:
        paragrafo_org = corpo.add_paragraph()
        paragrafo_org.paragraph_format.space_after = Pt(0)
        executar_org = paragrafo_org.add_run(f"Organização: {brincadeira.organizacao}")
        executar_org.font.name = FONTE
        executar_org.font.size = Pt(8.5)
        executar_org.font.italic = True
        executar_org.font.color.rgb = _rgb(CINZA_TEXTO)


def _capa(doc, plano: PlanoAula) -> None:
    faixa = _nova_tabela(doc, 1, 1, [LARGURA_UTIL])
    _sem_bordas(faixa)
    celula = faixa.rows[0].cells[0]
    _sombra_celula(celula, AZUL)
    _margens_celula(celula, topo=40, baixo=40)
    _texto_celula(celula, "PLANO DE AULA", tamanho=10, negrito=True, cor=BRANCO, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_paragraph()

    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(2)
    executar = paragrafo.add_run("Educação Infantil")
    executar.font.name = FONTE
    executar.font.size = Pt(11)
    executar.font.bold = True
    executar.font.color.rgb = _rgb(LARANJA)

    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(6)
    executar = paragrafo.add_run(plano.titulo)
    executar.font.name = FONTE
    executar.font.size = Pt(26)
    executar.font.bold = True
    executar.font.color.rgb = _rgb(AZUL_ESCURO)

    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(10)
    executar = paragrafo.add_run(plano.subtitulo)
    executar.font.name = FONTE
    executar.font.size = Pt(12)
    executar.font.color.rgb = _rgb(CINZA_TEXTO)

    selo = _nova_tabela(doc, 1, 1, [6.2])
    selo.alignment = WD_TABLE_ALIGNMENT.LEFT
    _sem_bordas(selo)
    celula_selo = selo.rows[0].cells[0]
    _sombra_celula(celula_selo, "FFF8E0")
    _margens_celula(celula_selo, topo=80, baixo=80)
    _texto_celula(celula_selo, "✔  Alinhado à BNCC 2018", tamanho=9, negrito=True, cor=LARANJA, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_page_break()


def render_plano(plano: PlanoAula, destino: Path) -> Path:
    doc = Document()

    secao = doc.sections[0]
    secao.page_width = Cm(21)
    secao.page_height = Cm(29.7)
    secao.left_margin = Cm(1.9)
    secao.right_margin = Cm(1.9)
    secao.top_margin = Cm(1.9)
    secao.bottom_margin = Cm(1.9)

    estilo = doc.styles["Normal"]
    estilo.font.name = FONTE
    estilo.font.size = Pt(9.5)

    _capa(doc, plano)

    _secao(doc, "01", "Identificação", "Dados gerais deste plano de aula.", AZUL)
    _tabela_identificacao(doc, plano)

    _secao(doc, "02", "Campos de experiência", "Este tema articula os campos previstos pela BNCC.", LARANJA)
    _tabela_dados(
        doc,
        ["", "Campo de experiência", "Por que entra nesta aula"],
        [[campo.icone, campo.nome, campo.justificativa] for campo in plano.campos_experiencia],
        [1.2, 6.2, LARGURA_UTIL - 7.4],
        LARANJA,
    )

    _secao(doc, "03", "Objetivos de aprendizagem", "O que a criança deverá aprender ao final da aula.", VERDE)
    for indice, objetivos in enumerate(plano.objetivos):
        _bloco_objetivos(doc, objetivos, CORES_MOMENTOS[indice % len(CORES_MOMENTOS)])

    _secao(doc, "04", "Habilidades da BNCC", "Habilidades mobilizadas ao longo da aula.", ROXO)
    _tabela_dados(
        doc,
        ["Código", "Descrição", "Campo"],
        [[h.codigo, h.descricao, h.campo_experiencia] for h in plano.habilidades],
        [2.5, LARGURA_UTIL - 6.4, 3.9],
        ROXO,
    )

    _secao(doc, "05", "Recursos e materiais", "Prepare todos os itens antes de iniciar a aula.", AZUL)
    _tabela_dados(
        doc,
        ["", "Material"],
        [[recurso.icone, recurso.descricao] for recurso in plano.recursos],
        [1.2, LARGURA_UTIL - 1.2],
        AZUL,
    )

    _secao(doc, "06", "Desenvolvimento da aula", "Sequência dos momentos da aula.", VERDE)
    tabela = _nova_tabela(doc, len(plano.desenvolvimento) + 1, 4, [1.3, 5.0, LARGURA_UTIL - 8.3, 2.0])
    _bordas_tabela(tabela, cor="E4E4EA")
    _cabecalho_tabela(tabela, ["Nº", "Momento", "O que acontece", "Tempo"], VERDE)

    for indice, momento in enumerate(plano.desenvolvimento, start=1):
        cor = CORES_MOMENTOS[(indice - 1) % len(CORES_MOMENTOS)]
        celula_numero = tabela.rows[indice].cells[0]
        _sombra_celula(celula_numero, cor)
        _margens_celula(celula_numero)
        _texto_celula(celula_numero, str(momento.ordem), tamanho=11, negrito=True, cor=BRANCO, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)

        celula_titulo = tabela.rows[indice].cells[1]
        _sombra_celula(celula_titulo, CINZA_CLARO)
        _margens_celula(celula_titulo)
        _texto_celula(celula_titulo, momento.titulo, tamanho=9, negrito=True, cor=AZUL_ESCURO)

        celula_descricao = tabela.rows[indice].cells[2]
        _sombra_celula(celula_descricao, BRANCO)
        _margens_celula(celula_descricao)
        _texto_celula(celula_descricao, momento.descricao, tamanho=9)

        celula_tempo = tabela.rows[indice].cells[3]
        _sombra_celula(celula_tempo, BRANCO)
        _margens_celula(celula_tempo)
        _texto_celula(celula_tempo, f"{momento.minutos} min", tamanho=9, negrito=True, cor=cor, alinhamento=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    _caixa_dica(doc, plano.dica)

    _secao(doc, "07", "Brincadeira & atividade para casa", "Extensões do tema para além da aula principal.", ROXO)
    _caixa_brincadeira(doc, plano)

    _secao(doc, "08", "Avaliação", "Rubrica formativa com indicadores por faixa etária.", AZUL)
    _paragrafo_texto(doc, plano.avaliacao.introducao, 9, CINZA_TEXTO, italico=True)
    _tabela_dados(
        doc,
        ["Critério observado", "Pré I", "Pré II"],
        [
            [indicador.criterio, indicador.pre_1, indicador.pre_2]
            for indicador in plano.avaliacao.indicadores
        ],
        [4.6, 6.3, LARGURA_UTIL - 10.9],
        AZUL,
    )

    _secao(
        doc,
        "09",
        "Adaptações e acessibilidade",
        "Sugestões para atender diferentes necessidades.",
        ROXO,
    )
    tabela = _nova_tabela(doc, 1, 1, [LARGURA_UTIL])
    _sem_bordas(tabela)
    celula = tabela.rows[0].cells[0]
    _sombra_celula(celula, CINZA_CLARO)
    _margens_celula(celula, topo=120, baixo=120, esquerda=160, direita=160)
    for indice, item in enumerate(plano.adaptacoes):
        paragrafo = celula.paragraphs[0] if indice == 0 else celula.add_paragraph()
        paragrafo.paragraph_format.space_after = Pt(3)
        executar = paragrafo.add_run(f"• {item}")
        executar.font.name = FONTE
        executar.font.size = Pt(9)
        executar.font.color.rgb = _rgb(CINZA_ESCURO)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)

    _secao(
        doc,
        "10",
        "Observações do(a) professor(a)",
        "Espaço para registrar reflexões após a aula.",
        VERDE,
    )
    tabela = _nova_tabela(doc, 1, 1, [LARGURA_UTIL])
    _sem_bordas(tabela)
    celula = tabela.rows[0].cells[0]
    _sombra_celula(celula, "FFFDF5")
    _margens_celula(celula, topo=140, baixo=140, esquerda=160, direita=160)
    if plano.observacoes_professor:
        _texto_celula(celula, plano.observacoes_professor, tamanho=9)
    else:
        for linha in range(5):
            paragrafo = celula.paragraphs[0] if linha == 0 else celula.add_paragraph()
            paragrafo.paragraph_format.space_after = Pt(8)
            executar = paragrafo.add_run("_" * 92)
            executar.font.name = FONTE
            executar.font.size = Pt(9)
            executar.font.color.rgb = _rgb(CINZA_LINHA)

    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_before = Pt(14)
    executar = paragrafo.add_run(
        "Plano gerado com apoio de IA a partir dos modelos da instituição. "
        "Base curricular: BNCC 2018. Revisar antes de aplicar."
    )
    executar.font.name = FONTE
    executar.font.size = Pt(7.5)
    executar.font.italic = True
    executar.font.color.rgb = _rgb(CINZA_TEXTO)

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destino)
    return destino


if __name__ == "__main__":
    from app.exemplo_pacote import pacote_exemplo
    from app.bncc import BaseBNCC
    from app.contract import resolver_pacote

    base = BaseBNCC()
    permitidos = {h.codigo for h in base.buscar(uso_escolar="Pré II")}
    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    saida = render_plano(pacote.plano, Path("storage/exemplo_plano.docx"))
    print(f"Gerado: {saida}")
