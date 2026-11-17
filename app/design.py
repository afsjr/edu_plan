"""Tokens de design compartilhados pelos renderizadores.

A fonte da verdade é ``app/design_tokens.json``, gerado por
``scripts/extrair_design_system.py`` a partir dos modelos da instituição.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
TOKENS_PATH = RAIZ / "app" / "design_tokens.json"


@lru_cache(maxsize=1)
def carregar_tokens() -> dict:
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


TOKENS = carregar_tokens()
CORES: dict[str, str] = TOKENS["cores"]
FONTES: dict = TOKENS["fontes"]
TIPOGRAFIA: dict = TOKENS["tipografia"]
LAYOUT: dict = TOKENS["layout"]

FONTE_TITULO: str = FONTES["titulo"]
FONTE_TEXTO: str = FONTES["texto"]
FONTE_FALLBACK: list[str] = FONTES["fallback"]


def cor(nome: str) -> str:
    """Retorna o hex do token ou o próprio valor, se já for hex."""
    return CORES.get(nome, nome)
