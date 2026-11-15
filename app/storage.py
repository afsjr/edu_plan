"""Histórico simples em SQLite e armazenamento local dos arquivos gerados."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
STORAGE = RAIZ / "storage"
GERACOES = STORAGE / "geracoes"
BANCO = STORAGE / "historico.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS geracoes (
    id TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL,
    uso_escolar TEXT NOT NULL,
    tema TEXT NOT NULL,
    observacoes TEXT NOT NULL DEFAULT '',
    provedor TEXT NOT NULL,
    avisos TEXT NOT NULL DEFAULT '[]',
    codigos TEXT NOT NULL DEFAULT '[]',
    caminho_plano TEXT NOT NULL,
    caminho_caderno TEXT NOT NULL
);
"""


@contextmanager
def _conexao():
    STORAGE.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def iniciar() -> None:
    with _conexao() as conexao:
        conexao.executescript(ESQUEMA)


def salvar(registro: dict) -> None:
    iniciar()
    with _conexao() as conexao:
        conexao.execute(
            """
            INSERT INTO geracoes (
                id, criado_em, uso_escolar, tema, observacoes, provedor,
                avisos, codigos, caminho_plano, caminho_caderno
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registro["id"],
                registro["criado_em"],
                registro["uso_escolar"],
                registro["tema"],
                registro.get("observacoes", ""),
                registro["provedor"],
                json.dumps(registro.get("avisos", []), ensure_ascii=False),
                json.dumps(registro.get("codigos", []), ensure_ascii=False),
                registro["caminho_plano"],
                registro["caminho_caderno"],
            ),
        )


def _linha_para_dict(linha: sqlite3.Row) -> dict:
    dados = dict(linha)
    dados["avisos"] = json.loads(dados.get("avisos") or "[]")
    dados["codigos"] = json.loads(dados.get("codigos") or "[]")
    return dados


def listar(limite: int = 50) -> list[dict]:
    iniciar()
    with _conexao() as conexao:
        linhas = conexao.execute(
            "SELECT * FROM geracoes ORDER BY criado_em DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return [_linha_para_dict(linha) for linha in linhas]


def obter(geracao_id: str) -> dict | None:
    iniciar()
    with _conexao() as conexao:
        linha = conexao.execute(
            "SELECT * FROM geracoes WHERE id = ?",
            (geracao_id,),
        ).fetchone()
    return _linha_para_dict(linha) if linha else None


def novo_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]


def diretorio_geracao(geracao_id: str) -> Path:
    caminho = GERACOES / geracao_id
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho
