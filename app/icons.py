"""Biblioteca de ícones/emoji usada nas atividades.

O mapa fica em `data/icons/icones.csv` e pode ser editado sem tocar no código.
Hoje o renderizador usa o emoji; a coluna `arquivo` está reservada para PNG/SVG.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV_PADRAO = RAIZ / "data" / "icons" / "icones.csv"
FALLBACK = "✨"

SINONIMOS = {
    "cor laranja": "cor_laranja",
    "cor azul": "azul",
    "cor verde": "verde",
    "cor amarela": "amarelo",
    "cor vermelha": "vermelho",
    "lapis de cor": "giz",
    "quebra cabeca": "quebra_cabeca",
    "ave": "passaro",
    "danca": "dancar",
}


def normalizar(texto: str) -> str:
    sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sem_acento).strip()


@dataclass(frozen=True)
class Icone:
    chave: str
    emoji: str
    arquivo: str
    categoria: str
    campo_bncc: str
    fonte: str
    licenca: str


class BancoIcones:
    def __init__(self, caminho: Path | str = CSV_PADRAO):
        self.caminho = Path(caminho)
        self._por_chave: dict[str, Icone] = {}
        self._carregar()

    def _carregar(self) -> None:
        with self.caminho.open(encoding="utf-8-sig", newline="") as arquivo:
            for linha in csv.DictReader(arquivo, delimiter=";"):
                chave = normalizar(linha.get("chave", ""))
                if not chave:
                    continue
                self._por_chave[chave] = Icone(
                    chave=chave,
                    emoji=(linha.get("emoji") or "").strip(),
                    arquivo=(linha.get("arquivo") or "").strip(),
                    categoria=(linha.get("categoria") or "").strip(),
                    campo_bncc=(linha.get("campo_bncc") or "").strip(),
                    fonte=(linha.get("fonte") or "").strip(),
                    licenca=(linha.get("licenca") or "").strip(),
                )

    def obter(self, palavra: str) -> Icone | None:
        chave = normalizar(palavra)
        if not chave:
            return None
        chave = normalizar(SINONIMOS.get(chave, chave))

        if chave in self._por_chave:
            return self._por_chave[chave]
        if chave.endswith("s") and chave[:-1] in self._por_chave:
            return self._por_chave[chave[:-1]]
        if chave + "s" in self._por_chave:
            return self._por_chave[chave + "s"]
        return None

    def emoji(self, palavra: str, fallback: str = FALLBACK) -> str:
        icone = self.obter(palavra)
        return icone.emoji if icone and icone.emoji else fallback

    def chaves(self) -> list[str]:
        return sorted(self._por_chave)

    def registros(self) -> list[Icone]:
        return [self._por_chave[chave] for chave in self.chaves()]


_BANCO: BancoIcones | None = None


def banco() -> BancoIcones:
    global _BANCO
    if _BANCO is None:
        _BANCO = BancoIcones()
    return _BANCO


def icone_para(palavra: str, fallback: str = FALLBACK) -> str:
    return banco().emoji(palavra, fallback)
