#!/usr/bin/env python3
"""Extrai as habilidades da BNCC do Ensino Fundamental — Anos Iniciais.

Fonte: BNCC_EI_EF_110518_versaofinal_site.pdf.

O PDF organiza as tabelas por ano/componente e usa códigos multi-ano em Arte
(EF15AR) e Educação Física (EF12EF/EF35EF). O extrator lê os blocos de texto,
separa cada código e mantém a descrição mais completa encontrada.

Uso:
    python3 scripts/extrair_bncc_ef.py
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

import pymupdf

RAIZ = Path(__file__).resolve().parents[1]
PDF_PADRAO = RAIZ / "exemplos base_inicial" / "BNCC_EI_EF_110518_versaofinal_site.pdf"
SAIDA = RAIZ / "data" / "bncc" / "bncc_ef.csv"

CODIGO_RE = re.compile(r"\((EF\d{2}[A-Z]{2}\d{2})\)")
CODIGO_VALIDO_RE = re.compile(r"^EF(0[1-5]|12|15|35)(LP|AR|EF|ER|MA|CI|GE|HI)\d{2}$")

CICLOS = {
    "01": ("1º ano", "1º ano", 1),
    "02": ("2º ano", "2º ano", 2),
    "03": ("3º ano", "3º ano", 3),
    "04": ("4º ano", "4º ano", 4),
    "05": ("5º ano", "5º ano", 5),
    "12": ("1º e 2º anos", "1º e 2º anos", 6),
    "15": ("1º ao 5º ano", "1º ao 5º ano", 7),
    "35": ("3º ao 5º ano", "3º ao 5º ano", 8),
}

COMPONENTES = {
    "LP": ("Língua Portuguesa", 1),
    "AR": ("Arte", 2),
    "EF": ("Educação Física", 3),
    "ER": ("Ensino Religioso", 4),
    "MA": ("Matemática", 5),
    "CI": ("Ciências", 6),
    "GE": ("Geografia", 7),
    "HI": ("História", 8),
}

ESPERADO_TOTAL = 574
ESPERADO_CICLO = {"01": 79, "02": 89, "03": 94, "04": 95, "05": 95, "12": 31, "15": 45, "35": 46}
ESPERADO_COMPONENTE = {"LP": 206, "AR": 26, "EF": 27, "ER": 33, "MA": 126, "CI": 48, "GE": 56, "HI": 52}

CABECALHO = [
    "ordem",
    "codigo",
    "etapa",
    "ano",
    "ciclo",
    "componente",
    "sigla_componente",
    "habilidade",
    "palavras_chave",
    "pagina_pdf",
    "fonte",
    "revisado",
    "observacao",
]

HEADERS_PDF = (
    "BASE NACIONAL",
    "ENSINO FUNDAMENTAL",
    "HABILIDADES",
    "UNIDADES TEMÁTICAS",
    "OBJETOS DE CONHECIMENTO",
    "1º ANO",
    "2º ANO",
    "3º ANO",
    "4º ANO",
    "5º ANO",
)

STOPWORDS = {
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
    "aluno", "alunos", "professor", "professores", "texto", "textos",
    "palavra", "palavras", "língua", "portuguesa", "habilidade", "habilidades",
    "objetivo", "objetivos", "ensino", "fundamental", "anos", "iniciais",
}


def limpar_texto(texto: str) -> str:
    """Normaliza espaços, corrige hifenização de quebra e remove invisíveis."""
    texto = texto.replace("\u00a0", " ").replace("\u00ad", "")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]

    juntas: list[str] = []
    for linha in linhas:
        if juntas and juntas[-1].endswith("-") and linha[:1].islower():
            if len(juntas[-1]) >= 2 and juntas[-1][-2].isalpha():
                juntas[-1] = juntas[-1][:-1] + linha
                continue
        juntas.append(linha)

    texto = " ".join(juntas)
    return re.sub(r"\s+", " ", texto).strip()


def gerar_palavras_chave(habilidade: str) -> str:
    termos: list[str] = []
    for palavra in re.findall(r"[A-Za-zÀ-ÿ]{4,}", habilidade.lower()):
        if palavra in STOPWORDS:
            continue
        if palavra not in termos:
            termos.append(palavra)
    return "; ".join(termos[:6])


def extrair_candidatos(pdf: Path) -> dict[str, dict]:
    documento = pymupdf.open(pdf)
    candidatos: dict[str, dict] = {}

    for pagina, page in enumerate(documento, start=1):
        for bloco in page.get_text("blocks"):
            texto = limpar_texto(bloco[4])
            achados = list(CODIGO_RE.finditer(texto))
            if not achados:
                continue

            for indice, achado in enumerate(achados):
                codigo = achado.group(1)
                ciclo = codigo[2:4]
                sigla = codigo[4:6]
                if ciclo not in CICLOS or sigla not in COMPONENTES:
                    continue

                fim = achados[indice + 1].start() if indice + 1 < len(achados) else len(texto)
                habilidade = texto[achado.end():fim].strip()
                if not habilidade:
                    continue

                anterior = candidatos.get(codigo)
                if anterior is None or len(habilidade) > len(anterior["habilidade"]):
                    candidatos[codigo] = {
                        "codigo": codigo,
                        "habilidade": habilidade,
                        "pagina_pdf": pagina,
                    }

    return candidatos


def validar_linha(linha: dict) -> list[str]:
    problemas: list[str] = []

    if not CODIGO_VALIDO_RE.fullmatch(linha["codigo"]):
        problemas.append("código fora do padrão do Fundamental I")
    if len(linha["habilidade"]) < 25:
        problemas.append("habilidade curta demais (possível truncamento)")
    if CODIGO_RE.search(linha["habilidade"]):
        problemas.append("habilidade contaminada com outro código")
    if any(header in linha["habilidade"].upper() for header in HEADERS_PDF):
        problemas.append("habilidade contaminada com cabeçalho do PDF")
    if "  " in linha["habilidade"]:
        problemas.append("espaços duplicados")
    if linha["habilidade"].endswith("-"):
        problemas.append("habilidade termina com hífen (possível quebra)")

    return problemas


def montar_linhas(candidatos: dict[str, dict]) -> list[dict]:
    linhas: list[dict] = []
    for codigo, dados in candidatos.items():
        ciclo = codigo[2:4]
        sigla = codigo[4:6]
        ano, descricao_ciclo, ordem_ciclo = CICLOS[ciclo]
        componente, ordem_componente = COMPONENTES[sigla]

        linha = {
            "codigo": codigo,
            "etapa": "Ensino Fundamental — Anos Iniciais",
            "ano": ano,
            "ciclo": ciclo,
            "componente": componente,
            "sigla_componente": sigla,
            "habilidade": dados["habilidade"],
            "palavras_chave": gerar_palavras_chave(dados["habilidade"]),
            "pagina_pdf": dados["pagina_pdf"],
            "fonte": "BNCC 2018 (PDF oficial)",
            "_ordem_ciclo": ordem_ciclo,
            "_ordem_componente": ordem_componente,
            "_descricao_ciclo": descricao_ciclo,
        }

        problemas = validar_linha(linha)
        linha["revisado"] = "S" if not problemas else "N"
        linha["observacao"] = "; ".join(problemas)
        linhas.append(linha)

    linhas.sort(
        key=lambda item: (
            item["_ordem_ciclo"],
            item["_ordem_componente"],
            item["codigo"],
        )
    )
    for indice, linha in enumerate(linhas, start=1):
        linha["ordem"] = indice
        linha.pop("_ordem_ciclo", None)
        linha.pop("_ordem_componente", None)
        linha.pop("_descricao_ciclo", None)
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
    escrever_csv(linhas, SAIDA)

    por_ciclo = collections.Counter(linha["ciclo"] for linha in linhas)
    por_componente = collections.Counter(linha["sigla_componente"] for linha in linhas)
    revisar = [linha for linha in linhas if linha["revisado"] != "S"]

    print(f"PDF: {PDF_PADRAO.name}")
    print(f"CSV: {SAIDA}")
    print(f"Linhas geradas: {len(linhas)}")
    print(f"Por ciclo: {dict(sorted(por_ciclo.items()))}")
    print(f"Por componente: {dict(sorted(por_componente.items()))}")
    print(f"Para revisar: {len(revisar)}")

    if len(linhas) != ESPERADO_TOTAL:
        print(
            f"Aviso: esperado {ESPERADO_TOTAL} habilidades, encontrado {len(linhas)}.",
            file=sys.stderr,
        )
    for ciclo, esperado in ESPERADO_CICLO.items():
        if por_ciclo.get(ciclo, 0) != esperado:
            print(
                f"Aviso: ciclo {ciclo} com {por_ciclo.get(ciclo, 0)}; esperado {esperado}.",
                file=sys.stderr,
            )
    for sigla, esperado in ESPERADO_COMPONENTE.items():
        if por_componente.get(sigla, 0) != esperado:
            print(
                f"Aviso: componente {sigla} com {por_componente.get(sigla, 0)}; esperado {esperado}.",
                file=sys.stderr,
            )
    for linha in revisar[:10]:
        print(f"  revisar {linha['codigo']}: {linha['observacao']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
