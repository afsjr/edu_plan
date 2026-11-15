#!/usr/bin/env python3
"""Valida o CSV da BNCC de Educação Infantil.

Uso:
    python3 scripts/validar_bncc.py
    python3 scripts/validar_bncc.py --pdf caminho/para/bncc.pdf
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PADRAO = ROOT / "data" / "bncc" / "bncc_ei.csv"
PDF_PADRAO = ROOT / "exemplos base_inicial" / "BNCC_EI_EF_110518_versaofinal_site.pdf"

CODE_RE = re.compile(r"^EI0[123](EO|CG|TS|EF|ET)\d{2}$")
CODE_SOLTO_RE = re.compile(r"EI0[123][A-Z]{2}\d{2}")

CABECALHO_ESPERADO = [
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

GRUPOS = {
    "EI01": ("Bebês", "zero a 1 ano e 6 meses", 29),
    "EI02": ("Crianças bem pequenas", "1 ano e 7 meses a 3 anos e 11 meses", 32),
    "EI03": ("Crianças pequenas", "4 anos a 5 anos e 11 meses", 32),
}

CAMPOS = {
    "EO": ("O eu, o outro e o nós", 20),
    "CG": ("Corpo, gestos e movimentos", 15),
    "TS": ("Traços, sons, cores e formas", 9),
    "EF": ("Escuta, fala, pensamento e imaginação", 27),
    "ET": ("Espaços, tempos, quantidades, relações e transformações", 22),
}

HEADERS_PDF = (
    "BASE NACIONAL",
    "EDUCAÇÃO INFANTIL",
    "OBJETIVOS DE APRENDIZAGEM",
    "CAMPO DE EXPERIÊNCIAS",
    "CRECHE",
    "PRÉ-ESCOLA",
)


class Relatorio:
    def __init__(self) -> None:
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, mensagem: str) -> None:
        self.erros.append(mensagem)

    def aviso(self, mensagem: str) -> None:
        self.avisos.append(mensagem)

    def imprimir(self) -> None:
        for aviso in self.avisos:
            print(f"AVISO: {aviso}")
        for erro in self.erros:
            print(f"ERRO: {erro}")
        if not self.erros:
            print("OK: base válida.")


def carregar(caminho: Path) -> tuple[list[str], list[dict]]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")
        cabecalho = leitor.fieldnames or []
        linhas = list(leitor)
    return cabecalho, linhas


def validar(caminho: Path, pdf: Path | None, relatorio: Relatorio) -> None:
    if not caminho.exists():
        relatorio.erro(f"CSV não encontrado: {caminho}")
        return

    cabecalho, linhas = carregar(caminho)

    if cabecalho != CABECALHO_ESPERADO:
        relatorio.erro(f"Cabeçalho inesperado: {cabecalho}")

    if len(linhas) != 93:
        relatorio.erro(f"Esperadas 93 linhas, encontradas {len(linhas)}")

    codigos = [linha.get("codigo", "") for linha in linhas]
    duplicados = [codigo for codigo, total in Counter(codigos).items() if total > 1]
    if duplicados:
        relatorio.erro(f"Códigos duplicados: {', '.join(sorted(duplicados))}")

    por_grupo: Counter[str] = Counter()
    por_campo: Counter[str] = Counter()
    ordem_esperada = 1

    for linha in linhas:
        codigo = linha.get("codigo", "")
        grupo_codigo = codigo[:4]
        sigla = codigo[4:6]

        if not CODE_RE.match(codigo):
            relatorio.erro(f"{codigo}: código fora do padrão EI0[123](EO|CG|TS|EF|ET)NN")
            continue

        por_grupo[grupo_codigo] += 1
        por_campo[sigla] += 1

        if linha.get("ordem") != str(ordem_esperada):
            relatorio.erro(f"{codigo}: ordem {linha.get('ordem')!r}, esperada {ordem_esperada}")
        ordem_esperada += 1

        grupo, faixa, _ = GRUPOS[grupo_codigo]
        if linha.get("grupo_etario") != grupo:
            relatorio.erro(f"{codigo}: grupo_etario {linha.get('grupo_etario')!r} != {grupo!r}")
        if linha.get("faixa_etaria") != faixa:
            relatorio.erro(f"{codigo}: faixa_etaria {linha.get('faixa_etaria')!r} != {faixa!r}")

        campo, _ = CAMPOS[sigla]
        if linha.get("campo_experiencia") != campo:
            relatorio.erro(f"{codigo}: campo_experiencia {linha.get('campo_experiencia')!r} != {campo!r}")
        if linha.get("sigla_campo") != sigla:
            relatorio.erro(f"{codigo}: sigla_campo {linha.get('sigla_campo')!r} != {sigla!r}")

        objetivo = linha.get("objetivo", "")
        if len(objetivo) < 25:
            relatorio.erro(f"{codigo}: objetivo curto demais ({len(objetivo)} caracteres)")
        if CODE_SOLTO_RE.search(objetivo):
            relatorio.erro(f"{codigo}: objetivo contaminado com outro código")
        if any(header in objetivo.upper() for header in HEADERS_PDF):
            relatorio.erro(f"{codigo}: objetivo contaminado com cabeçalho do PDF")
        if "  " in objetivo:
            relatorio.erro(f"{codigo}: objetivo com espaços duplicados")
        if objetivo.endswith("-"):
            relatorio.erro(f"{codigo}: objetivo termina com hífen")

        if linha.get("etapa") != "Educação Infantil":
            relatorio.erro(f"{codigo}: etapa inesperada {linha.get('etapa')!r}")
        if linha.get("fonte") != "BNCC 2018 (PDF oficial)":
            relatorio.erro(f"{codigo}: fonte inesperada {linha.get('fonte')!r}")
        if linha.get("revisado") not in {"S", "N"}:
            relatorio.erro(f"{codigo}: revisado deve ser S ou N")

        pagina = linha.get("pagina_pdf", "")
        if not pagina.isdigit() or not (47 <= int(pagina) <= 54):
            relatorio.erro(f"{codigo}: pagina_pdf fora da faixa 47-54 ({pagina!r})")

    for grupo_codigo, (_, _, esperado) in GRUPOS.items():
        if por_grupo[grupo_codigo] != esperado:
            relatorio.erro(
                f"Grupo {grupo_codigo}: esperadas {esperado} linhas, encontradas {por_grupo[grupo_codigo]}"
            )

    for sigla, (_, esperado) in CAMPOS.items():
        if por_campo[sigla] != esperado:
            relatorio.erro(
                f"Campo {sigla}: esperadas {esperado} linhas, encontradas {por_campo[sigla]}"
            )

    if pdf is not None:
        if not pdf.exists():
            relatorio.erro(f"PDF não encontrado para conferência: {pdf}")
        else:
            import pymupdf

            try:
                pymupdf.TOOLS.mupdf_display_errors(False)
                pymupdf.TOOLS.mupdf_display_warnings(False)
            except Exception:
                pass

            documento = pymupdf.open(pdf)
            texto = "\n".join(page.get_text() for page in documento)
            codigos_pdf = set(CODE_SOLTO_RE.findall(texto))
            codigos_csv = set(codigos)
            faltando = sorted(codigos_pdf - codigos_csv)
            sobrando = sorted(codigos_csv - codigos_pdf)
            if faltando:
                relatorio.erro(f"Códigos do PDF ausentes no CSV: {', '.join(faltando)}")
            if sobrando:
                relatorio.erro(f"Códigos do CSV ausentes no PDF: {', '.join(sobrando)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida o CSV da BNCC de Educação Infantil.")
    parser.add_argument("--csv", type=Path, default=CSV_PADRAO, help="CSV a validar")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="PDF oficial para conferência dos códigos (opcional; não versionado)",
    )
    args = parser.parse_args()

    pdf = args.pdf
    if pdf is None and PDF_PADRAO.exists():
        pdf = PDF_PADRAO

    relatorio = Relatorio()
    if pdf is None:
        relatorio.aviso("PDF não encontrado; conferência de códigos contra o PDF foi pulada.")
    validar(args.csv, pdf, relatorio)
    relatorio.imprimir()
    return 1 if relatorio.erros else 0


if __name__ == "__main__":
    sys.exit(main())
