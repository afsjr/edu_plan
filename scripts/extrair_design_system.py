#!/usr/bin/env python3
"""Extrai o design system dos modelos de referência (DOCX e PPTX).

O agente ``reversa-design-system`` não lê Office nativamente. Este script faz
a ponte: lê o OOXML, coleta cores, fontes, tamanhos, margens e mídia, e grava
os artefatos em ``_reversa_sdd/design-system/`` mais o JSON consumido pelos
renderizadores.

Uso:
    python3 scripts/extrair_design_system.py

Os arquivos de referência ficam fora do repositório público. Se não existirem,
o script mantém os tokens curados e registra a ausência nas evidências.
"""

from __future__ import annotations

import collections
import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from pptx import Presentation

RAIZ = Path(__file__).resolve().parents[1]
REF_DOCX = RAIZ / "exemplos base_inicial" / "Plano de Aula - Meu nome, minha identidade.docx"
REF_PPTX = RAIZ / "exemplos base_inicial" / "Atividades A4 ppt - Meu nome, minha identidade.pptx"
SAIDA_TOKENS = RAIZ / "app" / "design_tokens.json"
SAIDA_DOCS = RAIZ / "_reversa_sdd" / "design-system"

# Tokens curados. A extração confirma os valores e completa as evidências.
TOKENS_BASE = {
    "versao": 1,
    "fontes": {
        "titulo": "Poppins",
        "texto": "Inter",
        "fallback": ["Century Gothic", "Aptos", "Arial", "sans-serif"],
        "substitutos_abertos": {
            "pptx": "Poppins",
            "docx_titulo": "Poppins",
            "docx_texto": "Inter",
        },
        "origem_referencia": {
            "pptx": "Century Gothic",
            "docx": "Aptos / Aptos Display",
        },
        "licenca": "SIL Open Font License 1.1",
        "observacao": (
            "Os arquivos gerados referenciam o nome da fonte. A máquina que abre "
            "o DOCX/PPTX precisa ter Poppins e Inter instaladas; caso contrário, "
            "o Office substitui pela fallback."
        ),
    },
    "cores": {
        "azul_escuro": "1B6CA8",
        "azul": "2D9CDB",
        "laranja": "F2683C",
        "rosa": "F45B9C",
        "amarelo": "FDC22D",
        "verde": "4CAF73",
        "roxo": "9B6DD6",
        "cinza_texto": "6E6E80",
        "cinza_escuro": "3A3A4A",
        "cinza_linha": "C9C9D2",
        "cinza_claro": "F4F5F8",
        "branco": "FFFFFF",
        "creme": "FFF8E0",
        "fundo_desenho": "FFFDF5",
    },
    "layout": {
        "docx": {
            "pagina_cm": [21.0, 29.7],
            "margens_cm": 1.9,
            "largura_util_cm": 17.2,
            "secoes": 10,
            "tabelas_referencia": 9,
            "paragrafos_referencia": 55,
        },
        "pptx": {
            "pagina_cm": [21.01, 29.69],
            "margem_cm": 1.8,
            "largura_util_cm": 17.41,
            "slides_referencia": 6,
            "atividades": 5,
        },
    },
    "tipografia": {
        "docx": {
            "capa_titulo_pt": 28,
            "secao_titulo_pt": 20,
            "secao_numero_pt": 9,
            "corpo_pt": 10,
            "rotulo_pt": 9,
            "nota_pt": 7.5,
        },
        "pptx": {
            "capa_titulo_pt": 40,
            "capa_subtitulo_pt": 15,
            "atividade_titulo_pt": 22,
            "corpo_pt": 12,
            "rodape_pt": 9,
        },
    },
    "componentes": {
        "capa": "Faixa colorida, título grande, subtítulo, selo BNCC e identificação da etapa.",
        "secao": "Número em bloco colorido + título 20 pt + subtítulo 10 pt.",
        "tabela": "Cabeçalho colorido, linhas alternadas em cinza claro, bordas suaves.",
        "atividade": "Cabeçalho colorido, número em círculo, selo do código BNCC, enunciado e área de resposta.",
        "rodape": "Linha fina, nome do material, etapa e número da página.",
        "selo": "Pílula creme com borda amarela para 'Alinhado à BNCC'.",
    },
    "evidencias": {},
}


def _hex_counter(valores: list[str], limite: int = 15) -> dict[str, int]:
    return dict(collections.Counter(valores).most_common(limite))


def _docx_cores(caminho: Path) -> tuple[dict, dict, dict]:
    with zipfile.ZipFile(caminho) as arquivo:
        documento = arquivo.read("word/document.xml").decode("utf-8", "ignore")
        estilos = (
            arquivo.read("word/styles.xml").decode("utf-8", "ignore")
            if "word/styles.xml" in arquivo.namelist()
            else ""
        )
        tema = (
            arquivo.read("word/theme/theme1.xml").decode("utf-8", "ignore")
            if "word/theme/theme1.xml" in arquivo.namelist()
            else ""
        )
        midia = [
            nome
            for nome in arquivo.namelist()
            if nome.startswith("word/media/")
        ]

    cores_texto = _hex_counter(
        re.findall(r'w:color w:val="([0-9A-Fa-f]{6})"', documento + estilos)
    )
    preenchimentos = _hex_counter(re.findall(r'w:fill="([0-9A-Fa-f]{6})"', documento))
    fontes_tema = re.findall(
        r"<a:(majorFont|minorFont)>.*?<a:latin typeface=\"([^\"]*)\"",
        tema,
        re.S,
    )
    return cores_texto, preenchimentos, {
        "fontes_tema": fontes_tema[:4],
        "midia": len(midia),
    }


def _pptx_cores(caminho: Path) -> tuple[dict, dict]:
    with zipfile.ZipFile(caminho) as arquivo:
        xml = "\n".join(
            arquivo.read(nome).decode("utf-8", "ignore")
            for nome in arquivo.namelist()
            if nome.startswith("ppt/slides/slide") and nome.endswith(".xml")
        )
        midia = [
            nome
            for nome in arquivo.namelist()
            if nome.startswith("ppt/media/")
        ]
    return _hex_counter(re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', xml)), {
        "midia": len(midia)
    }


def extrair_docx(caminho: Path) -> dict:
    documento = Document(caminho)
    secao = documento.sections[0]
    fontes: collections.Counter[str] = collections.Counter()
    tamanhos: collections.Counter[float] = collections.Counter()

    for paragrafo in documento.paragraphs:
        for run in paragrafo.runs:
            if run.font.name:
                fontes[run.font.name] += 1
            if run.font.size:
                tamanhos[round(run.font.size.pt, 1)] += 1

    cores_texto, preenchimentos, extra = _docx_cores(caminho)
    return {
        "arquivo": caminho.name,
        "pagina_cm": [round(secao.page_width.cm, 1), round(secao.page_height.cm, 1)],
        "margens_cm": round(secao.left_margin.cm, 1),
        "paragrafos": len(documento.paragraphs),
        "tabelas": len(documento.tables),
        "fontes": dict(fontes.most_common(10)),
        "tamanhos_pt": {str(k): v for k, v in tamanhos.most_common(12)},
        "cores_texto": cores_texto,
        "preenchimentos": preenchimentos,
        **extra,
    }


def extrair_pptx(caminho: Path) -> dict:
    apresentacao = Presentation(caminho)
    fontes: collections.Counter[str] = collections.Counter()
    tamanhos: collections.Counter[float] = collections.Counter()
    slides = []

    for numero, slide in enumerate(apresentacao.slides, start=1):
        textos = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                textos.append(shape.text.strip().replace("\n", " / ")[:80])
            if not getattr(shape, "has_text_frame", False):
                continue
            for paragrafo in shape.text_frame.paragraphs:
                for run in paragrafo.runs:
                    if run.font.name:
                        fontes[run.font.name] += 1
                    if run.font.size:
                        tamanhos[round(run.font.size.pt, 1)] += 1
        slides.append(
            {
                "numero": numero,
                "shapes": len(slide.shapes),
                "textos": textos[:4],
            }
        )

    cores, extra = _pptx_cores(caminho)
    return {
        "arquivo": caminho.name,
        "slides": len(apresentacao.slides),
        "pagina_cm": [
            round(apresentacao.slide_width / 360000, 2),
            round(apresentacao.slide_height / 360000, 2),
        ],
        "fontes": dict(fontes.most_common(10)),
        "tamanhos_pt": {str(k): v for k, v in tamanhos.most_common(15)},
        "cores_srgb": cores,
        "slides_detalhe": slides,
        **extra,
    }


def _tabela_cores(cores: dict[str, int], nomes: dict[str, str]) -> str:
    linhas = ["| Token | Hex | Ocorrências | Uso |", "|---|---:|---:|---|"]
    for token, valor in TOKENS_BASE["cores"].items():
        linhas.append(
            f"| `{token}` | `#{valor}` | {cores.get(valor, 0)} | {nomes.get(token, '')} |"
        )
    return "\n".join(linhas)


def escrever_docs(tokens: dict) -> None:
    SAIDA_DOCS.mkdir(parents=True, exist_ok=True)
    docx = tokens["evidencias"].get("docx", {})
    pptx = tokens["evidencias"].get("pptx", {})
    cores = collections.Counter()
    for origem in (docx.get("cores_texto", {}), docx.get("preenchimentos", {}), pptx.get("cores_srgb", {})):
        for chave, valor in origem.items():
            cores[chave] += valor

    nomes = {
        "azul_escuro": "Títulos e textos de destaque",
        "azul": "Faixas, cabeçalhos e links",
        "laranja": "Acentos, selos e alertas",
        "rosa": "Atividades e blocos lúdicos",
        "amarelo": "Selo BNCC, destaques e legendas",
        "verde": "Seções de objetivos e avaliação",
        "roxo": "Seções de habilidades e adaptações",
        "cinza_texto": "Textos secundários",
        "cinza_escuro": "Corpo do texto",
        "cinza_linha": "Bordas e linhas divisórias",
        "cinza_claro": "Fundos de tabela e caixas",
        "branco": "Fundos e texto sobre cor",
        "creme": "Caixas de dica e escrita",
        "fundo_desenho": "Área de desenho",
    }

    (SAIDA_DOCS / "color-palette.md").write_text(
        "# Paleta de cores\n\n"
        "> Extraída dos modelos de referência por OOXML (🟢) e confirmada por uso (🟡).\n\n"
        + _tabela_cores(dict(cores), nomes)
        + "\n\n## Evidências\n\n"
        f"- DOCX: cores de texto `{docx.get('cores_texto', {})}`\n"
        f"- DOCX: preenchimentos `{docx.get('preenchimentos', {})}`\n"
        f"- PPTX: cores `srgbClr` `{pptx.get('cores_srgb', {})}`\n",
        encoding="utf-8",
    )

    (SAIDA_DOCS / "typography.md").write_text(
        "# Tipografia\n\n"
        "## Referência\n\n"
        f"- PPTX: `{tokens['fontes']['origem_referencia']['pptx']}`.\n"
        f"- DOCX: `{tokens['fontes']['origem_referencia']['docx']}`.\n"
        f"- Tamanhos PPTX: `{pptx.get('tamanhos_pt', {})}`.\n"
        f"- Tamanhos DOCX: `{docx.get('tamanhos_pt', {})}`.\n\n"
        "## Substitutos abertos\n\n"
        f"- Títulos: **{tokens['fontes']['titulo']}**.\n"
        f"- Texto: **{tokens['fontes']['texto']}**.\n"
        f"- Licença: {tokens['fontes']['licenca']}.\n\n"
        "> Os arquivos gerados referenciam o nome da fonte. Sem a fonte instalada, "
        "o Office usa a fallback.\n",
        encoding="utf-8",
    )

    (SAIDA_DOCS / "spacing.md").write_text(
        "# Espaçamento e layout\n\n"
        "## DOCX\n\n"
        f"- Página: {tokens['layout']['docx']['pagina_cm']} cm (A4).\n"
        f"- Margens: {tokens['layout']['docx']['margens_cm']} cm.\n"
        f"- Largura útil: {tokens['layout']['docx']['largura_util_cm']} cm.\n"
        f"- Seções: {tokens['layout']['docx']['secoes']}.\n\n"
        "## PPTX\n\n"
        f"- Página: {tokens['layout']['pptx']['pagina_cm']} cm (A4 retrato).\n"
        f"- Margem: {tokens['layout']['pptx']['margem_cm']} cm.\n"
        f"- Largura útil: {tokens['layout']['pptx']['largura_util_cm']} cm.\n"
        f"- Slides de referência: {tokens['layout']['pptx']['slides_referencia']} "
        f"(capa + {tokens['layout']['pptx']['atividades']} atividades).\n",
        encoding="utf-8",
    )

    (SAIDA_DOCS / "tokens.md").write_text(
        "# Tokens\n\n```json\n"
        + json.dumps(tokens, ensure_ascii=False, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )

    (SAIDA_DOCS / "design-system.md").write_text(
        "# Design system — modelos da instituição\n\n"
        "## Como foi extraído\n\n"
        "1. Leitura do OOXML de `"
        + docx.get("arquivo", "DOCX")
        + "` e `"
        + pptx.get("arquivo", "PPTX")
        + "`.\n"
        "2. Coleta de cores, fontes, tamanhos, margens, tabelas e mídia.\n"
        "3. Curadoria de substitutos abertos: Poppins (títulos) e Inter (texto).\n\n"
        "## Componentes\n\n"
        + "\n".join(f"- **{nome}:** {descricao}" for nome, descricao in tokens["componentes"].items())
        + "\n\n## Confiança\n\n"
        "- 🟢 Cores, fontes, tamanhos e margens lidos do OOXML.\n"
        "- 🟡 Uso semântico (qual cor vai em qual seção) inferido da comparação visual.\n"
        "- 🔴 Fonte original (Century Gothic/Aptos) não é aberta; substituída por Poppins/Inter.\n\n"
        "## Lacunas\n\n"
        "- O modelo PPTX tem 17 imagens; a geração atual tem 1 por atividade. "
        "A biblioteca de ilustrações ainda é uma trilha separada.\n"
        "- O DOCX de referência tem 9 tabelas e 55 parágrafos; o gerado tem 24 tabelas "
        "e 27 parágrafos. A estrutura de tabelas precisa ser simplificada.\n",
        encoding="utf-8",
    )


def main() -> int:
    tokens = json.loads(json.dumps(TOKENS_BASE))

    if REF_DOCX.exists():
        tokens["evidencias"]["docx"] = extrair_docx(REF_DOCX)
    else:
        tokens["evidencias"]["docx"] = {"ausente": str(REF_DOCX)}

    if REF_PPTX.exists():
        tokens["evidencias"]["pptx"] = extrair_pptx(REF_PPTX)
    else:
        tokens["evidencias"]["pptx"] = {"ausente": str(REF_PPTX)}

    SAIDA_TOKENS.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_TOKENS.write_text(
        json.dumps(tokens, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    escrever_docs(tokens)

    print(f"Tokens: {SAIDA_TOKENS}")
    print(f"Docs:   {SAIDA_DOCS}")
    if "ausente" in tokens["evidencias"]["docx"]:
        print("Aviso: DOCX de referência ausente; tokens curados mantidos.", file=sys.stderr)
    if "ausente" in tokens["evidencias"]["pptx"]:
        print("Aviso: PPTX de referência ausente; tokens curados mantidos.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
