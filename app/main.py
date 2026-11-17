"""Aplicação FastAPI: código BNCC → plano → validação → atividades."""

from __future__ import annotations

import logging
import re
import tempfile
import unicodedata
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.bncc import CAMPOS, GRUPOS, BaseBNCC, CodigoNaoEncontrado
from app.bncc_ef import COMPONENTES as COMPONENTES_EF
from app.bncc_ef import BaseBNCCEF
from app.config import carregar_env
from app.contract import CadernoAtividades, ErroContrato, PlanoAula
from app.llm import ErroLLM, RequisicaoGeracao, obter_cliente
from app.pipeline import gerar_atividades, gerar_plano
from app.render_docx import render_plano
from app.render_pptx import render_caderno

carregar_env()

RAIZ = Path(__file__).resolve().parents[1]
TEMPLATES = RAIZ / "app" / "templates"
ESTATICOS = RAIZ / "app" / "static"

USOS = ["Pré I", "Pré II"]
ANOS_EF = ["1º ano", "2º ano", "3º ano", "4º ano", "5º ano"]

MEDIA_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

logger = logging.getLogger("plano_aula")

app = FastAPI(title="Plano de Aula BNCC", version="0.2.0")
app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")
templates = Jinja2Templates(directory=TEMPLATES)

base_bncc = BaseBNCC()
base_bncc_ef = BaseBNCCEF()
CODIGOS = base_bncc.buscar(grupo="EI03")


def slug(texto: str) -> str:
    sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "-", sem_acento).strip("-")[:60] or "material"


def _contexto_index_ef(
    request: Request,
    erro: str | None = None,
    ano: str = "1º ano",
    codigo: str = "",
    observacoes: str = "",
) -> dict:
    codigos_por_componente = {
        sigla: [
            habilidade
            for habilidade in base_bncc_ef.habilidades
            if habilidade.sigla_componente == sigla
        ]
        for sigla in COMPONENTES_EF
    }
    return {
        "request": request,
        "anos": ANOS_EF,
        "componentes": COMPONENTES_EF,
        "codigos_por_componente": codigos_por_componente,
        "ano_padrao": ano,
        "codigo_padrao": codigo,
        "observacoes_padrao": observacoes,
        "erro": erro,
        "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
    }


def _contexto_index(
    request: Request,
    erro: str | None = None,
    uso: str = "Pré II",
    codigo: str = "",
    observacoes: str = "",
) -> dict:
    return {
        "request": request,
        "usos": USOS,
        "codigos": CODIGOS,
        "uso_padrao": uso,
        "codigo_padrao": codigo,
        "observacoes_padrao": observacoes,
        "erro": erro,
        "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", _contexto_index(request))


@app.get("/fund1", response_class=HTMLResponse)
def index_fund1(request: Request):
    return templates.TemplateResponse(
        request,
        "index_ef.html",
        _contexto_index_ef(request),
    )


@app.post("/gerar-plano-fund1", response_class=HTMLResponse)
def gerar_plano_fund1_route(
    request: Request,
    ano: str = Form(...),
    codigo: str = Form(...),
    observacoes: str = Form(""),
):
    requisicao = RequisicaoGeracao(
        uso_escolar=ano,
        codigo_ancora=codigo.strip().upper(),
        observacoes=observacoes.strip()[:500],
    )
    try:
        plano = gerar_plano(requisicao)
    except (CodigoNaoEncontrado, ErroContrato, ErroLLM, ValueError) as erro:
        logger.warning("Falha ao gerar plano do Fund. I: %s", erro)
        return templates.TemplateResponse(
            request,
            "index_ef.html",
            _contexto_index_ef(
                request,
                erro=str(erro),
                ano=ano,
                codigo=codigo,
                observacoes=observacoes,
            ),
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "plano.html",
        {
            "request": request,
            "plano": plano,
            "plano_json": plano.model_dump_json(),
            "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
        },
    )


@app.post("/gerar-plano", response_class=HTMLResponse)
def gerar_plano_route(
    request: Request,
    uso: str = Form(...),
    codigo: str = Form(...),
    observacoes: str = Form(""),
):
    requisicao = RequisicaoGeracao(
        uso_escolar=uso,
        codigo_ancora=codigo.strip().upper(),
        observacoes=observacoes.strip()[:500],
    )
    try:
        plano = gerar_plano(requisicao)
    except (CodigoNaoEncontrado, ErroContrato, ErroLLM, ValueError) as erro:
        logger.warning("Falha ao gerar plano: %s", erro)
        return templates.TemplateResponse(
            request,
            "index.html",
            _contexto_index(request, erro=str(erro), uso=uso, codigo=codigo, observacoes=observacoes),
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "plano.html",
        {
            "request": request,
            "plano": plano,
            "plano_json": plano.model_dump_json(),
            "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
        },
    )


@app.post("/gerar-atividades", response_class=HTMLResponse)
def gerar_atividades_route(request: Request, plano_json: str = Form(...)):
    try:
        plano = PlanoAula.model_validate_json(plano_json)
        caderno = gerar_atividades(plano)
    except (ErroContrato, ErroLLM, ValueError) as erro:
        logger.warning("Falha ao gerar atividades: %s", erro)
        return templates.TemplateResponse(
            request,
            "index.html",
            _contexto_index(request, erro=str(erro)),
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "atividades.html",
        {
            "request": request,
            "plano": plano,
            "plano_json": plano_json,
            "caderno": caderno,
            "caderno_json": caderno.model_dump_json(),
            "provedor": getattr(obter_cliente(), "nome", "desconhecido"),
        },
    )


def _baixar(conteudo: bytes, nome: str, media_type: str) -> Response:
    return Response(
        content=conteudo,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.post("/baixar-plano")
def baixar_plano(plano_json: str = Form(...)):
    try:
        plano = PlanoAula.model_validate_json(plano_json)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail="Plano inválido.") from erro

    with tempfile.TemporaryDirectory() as temporario:
        caminho = render_plano(plano, Path(temporario) / "plano_aula.docx")
        conteudo = caminho.read_bytes()
    return _baixar(conteudo, f"plano_{slug(plano.titulo)}.docx", MEDIA_TYPES[".docx"])


@app.post("/baixar-atividades")
def baixar_atividades(caderno_json: str = Form(...)):
    try:
        caderno = CadernoAtividades.model_validate_json(caderno_json)
    except ValueError as erro:
        raise HTTPException(status_code=400, detail="Caderno inválido.") from erro

    with tempfile.TemporaryDirectory() as temporario:
        caminho = render_caderno(caderno, Path(temporario) / "caderno_atividades.pptx")
        conteudo = caminho.read_bytes()
    return _baixar(conteudo, f"atividades_{slug(caderno.capa.titulo)}.pptx", MEDIA_TYPES[".pptx"])


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


@app.get("/bncc-ef", response_class=HTMLResponse)
def consultar_bncc_ef(
    request: Request,
    ano: str = "",
    componente: str = "",
    texto: str = "",
):
    erro = None
    try:
        resultados = base_bncc_ef.buscar(
            ano=ano or None,
            componente=componente or None,
            texto=texto or None,
        )
    except ValueError as falha:
        erro = str(falha)
        resultados = []

    return templates.TemplateResponse(
        request,
        "bncc_ef.html",
        {
            "request": request,
            "resultados": resultados,
            "anos": base_bncc_ef.anos_disponiveis(),
            "componentes": COMPONENTES_EF,
            "ano": ano,
            "componente": componente,
            "texto": texto,
            "erro": erro,
            "resumo": base_bncc_ef.resumo(),
        },
    )


@app.get("/saude")
def saude():
    return {
        "status": "ok",
        "base": base_bncc.resumo(),
        "base_ef": base_bncc_ef.resumo(),
    }
