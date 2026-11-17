#!/usr/bin/env python3
"""Valida a base da BNCC do Ensino Fundamental — Anos Iniciais.

Uso:
    python3 scripts/validar_bncc_ef.py
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "bncc" / "bncc_ef.csv"

ESPERADO_TOTAL = 574
ESPERADO_CICLO = {"01": 79, "02": 89, "03": 94, "04": 95, "05": 95, "12": 31, "15": 45, "35": 46}
ESPERADO_COMPONENTE = {"LP": 206, "AR": 26, "EF": 27, "ER": 33, "MA": 126, "CI": 48, "GE": 56, "HI": 52}

CODIGO_RE = re.compile(r"^EF(0[1-5]|12|15|35)(LP|AR|EF|ER|MA|CI|GE|HI)\d{2}$")


def main() -> int:
    if not CSV.exists():
        print(f"CSV não encontrado: {CSV}", file=sys.stderr)
        return 1

    with CSV.open(encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo, delimiter=";"))

    problemas: list[str] = []
    codigos = [linha["codigo"].strip() for linha in linhas]
    duplicados = [codigo for codigo, total in collections.Counter(codigos).items() if total > 1]
    if duplicados:
        problemas.append(f"códigos duplicados: {', '.join(duplicados[:10])}")

    por_ciclo = collections.Counter(linha["ciclo"].strip() for linha in linhas)
    por_componente = collections.Counter(linha["sigla_componente"].strip() for linha in linhas)

    if len(linhas) != ESPERADO_TOTAL:
        problemas.append(f"total {len(linhas)}; esperado {ESPERADO_TOTAL}")
    for ciclo, esperado in ESPERADO_CICLO.items():
        if por_ciclo.get(ciclo, 0) != esperado:
            problemas.append(f"ciclo {ciclo}: {por_ciclo.get(ciclo, 0)}; esperado {esperado}")
    for sigla, esperado in ESPERADO_COMPONENTE.items():
        if por_componente.get(sigla, 0) != esperado:
            problemas.append(f"componente {sigla}: {por_componente.get(sigla, 0)}; esperado {esperado}")

    for linha in linhas:
        codigo = linha["codigo"].strip()
        if not CODIGO_RE.fullmatch(codigo):
            problemas.append(f"código inválido: {codigo}")
        if linha["revisado"].strip() != "S":
            problemas.append(f"{codigo}: revisado={linha['revisado']} ({linha['observacao']})")
        if len(linha["habilidade"].strip()) < 25:
            problemas.append(f"{codigo}: habilidade curta")
        if linha["ciclo"].strip() != codigo[2:4]:
            problemas.append(f"{codigo}: ciclo divergente")
        if linha["sigla_componente"].strip() != codigo[4:6]:
            problemas.append(f"{codigo}: componente divergente")

    print(f"CSV: {CSV}")
    print(f"Linhas: {len(linhas)}")
    print(f"Por ciclo: {dict(sorted(por_ciclo.items()))}")
    print(f"Por componente: {dict(sorted(por_componente.items()))}")
    print(f"Problemas: {len(problemas)}")
    for problema in problemas[:20]:
        print(f"  - {problema}")

    return 1 if problemas else 0


if __name__ == "__main__":
    raise SystemExit(main())
