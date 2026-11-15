#!/usr/bin/env python3
"""Extrai os objetivos de aprendizagem e desenvolvimento da Educação Infantil
da BNCC (PDF oficial) para um CSV estruturado.

Fonte: BNCC_EI_EF_110518_versaofinal_site.pdf (páginas 47-54, tabelas detalhadas).

Uso:
    python3 scripts/extrair_bncc_ei.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF_PADRAO = ROOT / "exemplos base_inicial" / "BNCC_EI_EF_110518_versaofinal_site.pdf"
SAIDA = ROOT / "data" / "bncc" / "bncc_ei.csv"

# Apenas as tabelas detalhadas por campo de experiência (a página 28 é o quadro-resumo).
PAGINAS_DETALHADAS = range(47, 55)

try:
    pymupdf.TOOLS.mupdf_display_errors(False)
    pymupdf.TOOLS.mupdf_display_warnings(False)
except Exception:
    pass

CODE_RE = re.compile(r"^\((EI0[123][A-Z]{2}\d{2})\)\s*(.+)$", re.S)
CODE_SOLTO_RE = re.compile(r"EI0[123][A-Z]{2}\d{2}")

GRUPOS = {
    "EI01": ("Bebês", "zero a 1 ano e 6 meses"),
    "EI02": ("Crianças bem pequenas", "1 ano e 7 meses a 3 anos e 11 meses"),
    "EI03": ("Crianças pequenas", "4 anos a 5 anos e 11 meses"),
}

CAMPOS = {
    "EO": ("O eu, o outro e o nós", 1),
    "CG": ("Corpo, gestos e movimentos", 2),
    "TS": ("Traços, sons, cores e formas", 3),
    "EF": ("Escuta, fala, pensamento e imaginação", 4),
    "ET": ("Espaços, tempos, quantidades, relações e transformações", 5),
}

STOPWORDS = {
    # artigos, preposições e conectivos
    "para", "pela", "pelo", "pelos", "pelas", "como", "com", "sem", "sobre",
    "entre", "quando", "onde", "qual", "quais", "que", "dos", "das", "nos",
    "nas", "aos", "umas", "uns", "uma", "um", "ao", "à", "às", "por", "após",
    "antes", "depois", "durante", "através", "também", "cada", "todos",
    "todas", "alguns", "algumas", "outros", "outras", "outro", "outra",
    "esse", "essa", "este", "esta", "isso", "aquilo", "mais", "menos",
    "muito", "pouco", "mesma", "mesmo", "forma", "formas", "meio", "vez",
    "partir", "etc", "não", "sim", "bem", "estar", "ser", "ter", "fazer",
    "uso", "seus", "suas", "seu", "sua", "diversos", "diversas",
    "diferentes", "maneiras", "situações", "contextos", "ações", "atividades",
    # termos genéricos que não ajudam na busca
    "crianças", "adultos", "pessoas", "colegas", "corpo", "espaços", "objetos",
    "brincadeiras", "interações", "desenvolvendo", "utilizando", "reconhecendo",
    "percebendo", "demonstrar", "expressar", "identificar", "participar",
    "realizar", "utilizar", "reconhecer", "comunicar", "ampliar", "criar",
    "explorar", "experimentar", "manifestar", "respeitar", "comparar",
    "observar", "relacionar", "registrar", "contar", "nomear", "imitar",
    "faixa", "etária", "possibilidades", "diversificadas", "variados",
}

CABECALHO = [
    "ordem",
    "codigo",
    "etapa",
    "grupo_etario",
    "faixa_etaria",
    "campo_experiencia",
    "sigla_campo",
    "objetivo",
    "palavras_chave",
    "pagina_pdf",
    "fonte",
    "revisado",
    "observacao",
]

HEADERS_PDF = (
    "BASE NACIONAL",
    "EDUCAÇÃO INFANTIL",
    "OBJETIVOS DE APRENDIZAGEM",
    "CAMPO DE EXPERIÊNCIAS",
    "CRECHE",
    "PRÉ-ESCOLA",
)


def limpar_texto(texto: str) -> str:
    """Normaliza espaços, remove hifenização de quebra de linha e caracteres invisíveis."""
    texto = texto.replace("\u00a0", " ").replace("\u00ad", "")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]

    juntas: list[str] = []
    for linha in linhas:
        if juntas and juntas[-1].endswith("-") and linha[:1].islower():
            # "vivên-" + "cias" -> "vivências"; "pré-" + "escolar" permanece com hífen
            if len(juntas[-1]) >= 2 and juntas[-1][-2].isalpha():
                juntas[-1] = juntas[-1][:-1] + linha
                continue
        juntas.append(linha)

    texto = " ".join(juntas)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def gerar_palavras_chave(objetivo: str, campo: str) -> str:
    """Extrai termos de busca do próprio objetivo. É um apoio, não dado oficial."""
    termos: list[str] = []
    for palavra in re.findall(r"[A-Za-zÀ-ÿ]{4,}", objetivo.lower()):
        if palavra in STOPWORDS:
            continue
        if palavra not in termos:
            termos.append(palavra)
    return "; ".join(termos[:6])


def extrair_candidatos(pdf: Path) -> dict[str, dict]:
    doc = pymupdf.open(pdf)
    candidatos: dict[str, dict] = {}

    for pagina, page in enumerate(doc, start=1):
        if pagina not in PAGINAS_DETALHADAS:
            continue
        for bloco in page.get_text("blocks"):
            texto = bloco[4].strip()
            casamento = CODE_RE.match(texto)
            if not casamento:
                continue

            codigo = casamento.group(1)
            objetivo = limpar_texto(casamento.group(2))
            if not objetivo:
                continue

            anterior = candidatos.get(codigo)
            # Fica com a descrição mais completa (a tabela detalhada vence o resumo).
            if anterior is None or len(objetivo) > len(anterior["objetivo"]):
                candidatos[codigo] = {
                    "codigo": codigo,
                    "objetivo": objetivo,
                    "pagina_pdf": pagina,
                }

    return candidatos


def codigos_no_texto_integral(pdf: Path) -> set[str]:
    doc = pymupdf.open(pdf)
    texto = "\n".join(page.get_text() for page in doc)
    return set(CODE_SOLTO_RE.findall(texto))


def validar_linha(linha: dict) -> list[str]:
    problemas: list[str] = []

    if not re.fullmatch(r"EI0[123](EO|CG|TS|EF|ET)\d{2}", linha["codigo"]):
        problemas.append("código fora do padrão")
    if len(linha["objetivo"]) < 25:
        problemas.append("objetivo curto demais (possível truncamento)")
    if CODE_SOLTO_RE.search(linha["objetivo"]):
        problemas.append("objetivo contaminado com outro código")
    if any(h in linha["objetivo"].upper() for h in HEADERS_PDF):
        problemas.append("objetivo contaminado com cabeçalho do PDF")
    if "  " in linha["objetivo"]:
        problemas.append("espaços duplicados")
    if linha["objetivo"].endswith("-"):
        problemas.append("objetivo termina com hífen (possível quebra)")

    return problemas


def montar_linhas(candidatos: dict[str, dict]) -> list[dict]:
    linhas: list[dict] = []
    for codigo, dados in candidatos.items():
        grupo_codigo = codigo[:4]
        sigla = codigo[4:6]

        grupo, faixa = GRUPOS[grupo_codigo]
        campo, ordem_campo = CAMPOS[sigla]

        linha = {
            "codigo": codigo,
            "etapa": "Educação Infantil",
            "grupo_etario": grupo,
            "faixa_etaria": faixa,
            "campo_experiencia": campo,
            "sigla_campo": sigla,
            "objetivo": dados["objetivo"],
            "palavras_chave": gerar_palavras_chave(dados["objetivo"], campo),
            "pagina_pdf": dados["pagina_pdf"],
            "fonte": "BNCC 2018 (PDF oficial)",
        }

        problemas = validar_linha(linha)
        linha["revisado"] = "S" if not problemas else "N"
        linha["observacao"] = "; ".join(problemas)
        linha["_ordem_campo"] = ordem_campo
        linha["_grupo"] = grupo_codigo
        linhas.append(linha)

    linhas.sort(key=lambda x: (x["_ordem_campo"], x["_grupo"], x["codigo"]))
    for i, linha in enumerate(linhas, start=1):
        linha["ordem"] = i
        linha.pop("_ordem_campo", None)
        linha.pop("_grupo", None)
    return linhas


def escrever_csv(linhas: list[dict], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=CABECALHO,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({chave: linha[chave] for chave in CABECALHO})


def main() -> int:
    if not PDF_PADRAO.exists():
        print(f"PDF não encontrado: {PDF_PADRAO}", file=sys.stderr)
        return 1

    candidatos = extrair_candidatos(PDF_PADRAO)
    linhas = montar_linhas(candidatos)

    codigos_pdf = codigos_no_texto_integral(PDF_PADRAO)
    codigos_csv = {linha["codigo"] for linha in linhas}

    faltando = sorted(codigos_pdf - codigos_csv)
    sobrando = sorted(codigos_csv - codigos_pdf)

    escrever_csv(linhas, SAIDA)

    print(f"PDF: {PDF_PADRAO.name}")
    print(f"CSV: {SAIDA}")
    print(f"Linhas geradas: {len(linhas)}")
    print(f"Códigos únicos no PDF: {len(codigos_pdf)}")
    print(f"Códigos sem linha no CSV: {len(faltando)}")
    if faltando:
        print("  faltando:", ", ".join(faltando))
    print(f"Códigos no CSV fora do PDF: {len(sobrando)}")
    if sobrando:
        print("  sobrando:", ", ".join(sobrando))

    por_grupo: dict[str, int] = {}
    por_campo: dict[str, int] = {}
    pendentes = []
    for linha in linhas:
        por_grupo[linha["codigo"][:4]] = por_grupo.get(linha["codigo"][:4], 0) + 1
        por_campo[linha["sigla_campo"]] = por_campo.get(linha["sigla_campo"], 0) + 1
        if linha["revisado"] != "S":
            pendentes.append(linha["codigo"])

    print("Por grupo:", dict(sorted(por_grupo.items())))
    print("Por campo:", dict(sorted(por_campo.items())))
    print(f"Linhas sinalizadas para revisão: {len(pendentes)}")
    if pendentes:
        print("  ", ", ".join(pendentes))

    return 0 if not faltando and not sobrando else 2


if __name__ == "__main__":
    raise SystemExit(main())
