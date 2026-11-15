"""Aplicação FastAPI do MVP: gerar o pacote, consultar a BNCC e baixar arquivos."""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import storage
from app.bncc import CAMPOS, GRUPOS, BaseBNCC
from app.config import carregar_env
from app.contract import ErroContrato
from app.llm import ErroLLM, RequisicaoGeracao, obter_cliente
from app.pipeline import gerar_e_salvar, gerar_zip

carregar_env()

RAIZ = Path(__file__).resolve().parents[1]
TEMPLATES = RAIZ / "app" / "templates"
ESTATICOS = RAIZ / "app" / "static"

TEMA_PADRAO = "Meu nome, minha identidade"
USOS = ["Pré I", "Pré II"]

MEDIA_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

logger = logging.getLogger("plano_aula")

app = FastAPI(title="Plano de Aula BNCC", version="0.1.0")
app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")
templates = Jinja2Templates(directory=TEMPLATES)

base_bncc = BaseBNCC()


def slug(texto: str) -> str:
    sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "-", sem_acento).strip("-")[:60] or "material"


def modo_demo() -> bool:
    """No Vercel não há disco persistente: o modo demo devolve um ZIP."""
    return os.getenv("VERCEL_DEMO") == "1"


def _contexto_base(request: Request, **extra) -> dict:
    contexto = {
        "request": request,
        "usos": USOS,
        "tema_padrao": TEMA_PADRAO,
        "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
        "erro": None,
        "modo_demo": modo_demo(),
        "recentes": [] if modo_demo() else storage.listar(5),
    }
    contexto.update(extra)
    return contexto


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", _contexto_base(request))


@app.post("/gerar")
def gerar(
    request: Request,
    uso: str = Form(...),
    tema: str = Form(...),
    observacoes: str = Form(""),
):
    tema = tema.strip()[:120]
    observacoes = observacoes.strip()[:500]

    if not tema:
        return templates.TemplateResponse(
            request,
            "index.html",
            _contexto_base(request, erro="Descreva o tema da aula."),
            status_code=400,
        )

    requisicao = RequisicaoGeracao(
        uso_escolar=uso,
        tema=tema,
        observacoes=observacoes,
    )

    try:
        if modo_demo():
            conteudo = gerar_zip(requisicao)
            nome = f"pacote_{slug(tema)}.zip"
            return Response(
                content=conteudo,
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="{nome}"'},
            )

        resultado = gerar_e_salvar(requisicao)
    except (ErroContrato, ErroLLM, ValueError) as erro:
        logger.warning("Falha na geração: %s", erro)
        return templates.TemplateResponse(
            request,
            "index.html",
            _contexto_base(
                request,
                erro=str(erro),
                tema_padrao=tema,
            ),
            status_code=400,
        )
    except Exception:  # pragma: no cover - proteção para o demo
        logger.exception("Erro inesperado na geração")
        return templates.TemplateResponse(
            request,
            "index.html",
            _contexto_base(
                request,
                erro="Não foi possível gerar o material. Tente novamente.",
                tema_padrao=tema,
            ),
            status_code=500,
        )

    return RedirectResponse(url=f"/resultado/{resultado['id']}", status_code=303)


def _carregar_pacote(caminho_plano: str) -> dict | None:
    caminho = Path(caminho_plano).parent / "pacote.json"
    if not caminho.exists():
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


@app.get("/resultado/{geracao_id}", response_class=HTMLResponse)
def resultado(request: Request, geracao_id: str):
    if modo_demo():
        raise HTTPException(status_code=404, detail="O modo demonstração não guarda histórico.")

    registro = storage.obter(geracao_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Geração não encontrada.")

    pacote = _carregar_pacote(registro["caminho_plano"])

    return templates.TemplateResponse(
        request,
        "resultado.html",
        {
            "request": request,
            "registro": registro,
            "pacote": pacote,
        },
    )


@app.get("/historico", response_class=HTMLResponse)
def historico(request: Request):
    return templates.TemplateResponse(
        request,
        "historico.html",
        {
            "request": request,
            "modo_demo": modo_demo(),
            "geracoes": [] if modo_demo() else storage.listar(100),
        },
    )


@app.get("/download/{geracao_id}/{tipo}")
def download(geracao_id: str, tipo: str):
    if modo_demo():
        raise HTTPException(status_code=404, detail="O modo demonstração não guarda histórico.")

    if tipo not in {"plano", "caderno"}:
        raise HTTPException(status_code=404, detail="Arquivo desconhecido.")

    registro = storage.obter(geracao_id)
    if not registro:
        raise HTTPException(status_code=404, detail="Geração não encontrada.")

    chave = "caminho_plano" if tipo == "plano" else "caminho_caderno"
    caminho = Path(registro[chave])
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no disco.")

    nome = f"{tipo}_{slug(registro['tema'])}{caminho.suffix}"
    return FileResponse(
        caminho,
        media_type=MEDIA_TYPES.get(caminho.suffix, "application/octet-stream"),
        filename=nome,
    )


@app.get("/bncc", response_class=HTMLResponse)
def consultar_bncc(
    request: Request,
    grupo: str = "",
    campo: str = "",
    texto: str = "",
):
    erro = None
    try:
        resultados = base_bncc.buscar(
            grupo=grupo or None,
            campo=campo or None,
            texto=texto or None,
        )
    except ValueError as falha:
        erro = str(falha)
        resultados = []

    return templates.TemplateResponse(
        request,
        "bncc.html",
        {
            "request": request,
            "resultados": resultados,
            "grupos": GRUPOS,
            "campos": CAMPOS,
            "grupo": grupo,
            "campo": campo,
            "texto": texto,
            "erro": erro,
            "resumo": base_bncc.resumo(),
        },
    )


@app.get("/saude")
def saude():
    return {
        "status": "ok",
        "base": base_bncc.resumo(),
    }
