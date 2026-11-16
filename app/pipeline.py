"""Pipeline em duas etapas: plano → validação → atividades."""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app import image as image_service
from app import storage
from app.bncc import BaseBNCC
from app.config import carregar_env
from app.contract import (
    SCHEMA_CADERNO,
    SCHEMA_PLANO,
    CadernoAtividades,
    ErroContrato,
    Pacote,
    PlanoAula,
    exportar_schemas,
    resolver_caderno,
    resolver_plano,
    validar_plano,
)
from app.llm import ErroLLM, LLMClient, RequisicaoGeracao, obter_cliente
from app.render_docx import render_plano
from app.render_pptx import render_caderno

carregar_env()

logger = logging.getLogger("plano_aula.pipeline")


def _schemas() -> tuple[dict, dict]:
    if not SCHEMA_PLANO.exists() or not SCHEMA_CADERNO.exists():
        exportar_schemas()
    return (
        json.loads(SCHEMA_PLANO.read_text(encoding="utf-8")),
        json.loads(SCHEMA_CADERNO.read_text(encoding="utf-8")),
    )


def gerar_plano(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
    base: BaseBNCC | None = None,
) -> PlanoAula:
    base = base or BaseBNCC()
    cliente = cliente or obter_cliente()

    candidatos = base.selecionar_codigos(
        requisicao.codigo_ancora,
        requisicao.uso_escolar,
        total=7,
        campos=4,
    )
    if len(candidatos) < 7 or len({h.sigla_campo for h in candidatos}) < 4:
        raise ErroContrato(
            "A base não possui códigos suficientes para montar o plano desta turma."
        )

    schema_plano, _ = _schemas()
    permitidos = {habilidade.codigo for habilidade in candidatos}
    feedback: list[str] = []
    ultimo_erro: Exception | None = None

    for _ in range(3):
        try:
            gerado = cliente.gerar_plano(
                requisicao,
                candidatos,
                schema_plano,
                feedback=feedback,
            )
            return resolver_plano(gerado, base, permitidos, requisicao.codigo_ancora)
        except (ErroContrato, ErroLLM, ValueError) as erro:
            ultimo_erro = erro
            feedback.append(str(erro))

    raise ErroContrato(
        f"Não foi possível gerar um plano válido após 3 tentativas: {ultimo_erro}"
    )


def gerar_atividades(
    plano: PlanoAula,
    cliente: LLMClient | None = None,
) -> CadernoAtividades:
    base = BaseBNCC()
    cliente = cliente or obter_cliente()
    _, schema_caderno = _schemas()
    feedback: list[str] = []
    ultimo_erro: Exception | None = None

    for _ in range(3):
        try:
            gerado = cliente.gerar_atividades(
                plano,
                schema_caderno,
                feedback=feedback,
            )
            caderno = resolver_caderno(gerado, plano, base)
            return enriquecer_imagens(caderno, plano)
        except (ErroContrato, ErroLLM, ValueError) as erro:
            ultimo_erro = erro
            feedback.append(str(erro))

    raise ErroContrato(
        f"Não foi possível gerar atividades válidas após 3 tentativas: {ultimo_erro}"
    )


def enriquecer_imagens(
    caderno: CadernoAtividades,
    plano: PlanoAula,
) -> CadernoAtividades:
    """Gera no máximo IMAGE_MAX imagens por pacote, sem contar/letras."""
    if not image_service.disponivel():
        return caderno

    try:
        maximo = int(os.getenv("IMAGE_MAX") or "1")
    except ValueError:
        maximo = 1
    maximo = max(0, min(maximo, 2))
    if maximo == 0:
        return caderno

    candidatas = {
        atividade.numero
        for atividade in caderno.atividades
        if atividade.imagem_alt
        and atividade.tipo not in {"contar", "cobrir_palavra"}
        and not atividade.imagem_base64
    }
    if not candidatas:
        return caderno

    geradas = 0
    atividades = []
    for atividade in caderno.atividades:
        if geradas < maximo and atividade.numero in candidatas:
            try:
                prompt = image_service.montar_prompt(
                    atividade.imagem_alt,
                    plano.identificacao.tema,
                )
                imagem = image_service.gerar_imagem(prompt)
                atividades.append(
                    atividade.model_copy(update={"imagem_base64": imagem})
                )
                geradas += 1
                logger.info("Imagem gerada para a atividade %s", atividade.numero)
            except image_service.ErroImagem as erro:
                logger.warning(
                    "Falha ao gerar imagem da atividade %s: %s",
                    atividade.numero,
                    erro,
                )
                atividades.append(atividade)
        else:
            atividades.append(atividade)

    return caderno.model_copy(update={"atividades": atividades})


def gerar_pacote(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
    base: BaseBNCC | None = None,
) -> Pacote:
    cliente = cliente or obter_cliente()
    plano = gerar_plano(requisicao, cliente=cliente, base=base)
    caderno = gerar_atividades(plano, cliente=cliente)
    return Pacote(plano=plano, caderno=caderno, avisos=validar_plano(plano))


def gerar_zip(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
) -> bytes:
    pacote = gerar_pacote(requisicao, cliente=cliente)
    with tempfile.TemporaryDirectory() as temporario:
        pasta = Path(temporario)
        plano = render_plano(pacote.plano, pasta / "plano_aula.docx")
        caderno = render_caderno(pacote.caderno, pasta / "caderno_atividades.pptx")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as arquivo_zip:
            arquivo_zip.write(plano, arcname="plano_aula.docx")
            arquivo_zip.write(caderno, arcname="caderno_atividades.pptx")
        return buffer.getvalue()


def gerar_e_salvar(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
) -> dict:
    cliente = cliente or obter_cliente()
    pacote = gerar_pacote(requisicao, cliente=cliente)

    geracao_id = storage.novo_id()
    destino = storage.diretorio_geracao(geracao_id)
    caminho_plano = render_plano(pacote.plano, destino / "plano_aula.docx")
    caminho_caderno = render_caderno(pacote.caderno, destino / "caderno_atividades.pptx")
    (destino / "pacote.json").write_text(pacote.model_dump_json(indent=2), encoding="utf-8")

    registro = {
        "id": geracao_id,
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "uso_escolar": requisicao.uso_escolar,
        "tema": pacote.plano.identificacao.tema,
        "observacoes": requisicao.observacoes,
        "provedor": getattr(cliente, "nome", "desconhecido"),
        "avisos": pacote.avisos,
        "codigos": [habilidade.codigo for habilidade in pacote.plano.habilidades],
        "caminho_plano": str(caminho_plano),
        "caminho_caderno": str(caminho_caderno),
    }
    storage.salvar(registro)
    return {**registro, "pacote": pacote}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera plano e atividades a partir de um código BNCC.")
    parser.add_argument("--codigo", required=True, help="Código âncora, ex.: EI03EF01")
    parser.add_argument("--uso", default="Pré II", help="Pré I, Pré II, Maternal ou Berçário")
    parser.add_argument("--observacoes", default="", help="Observações para a geração")
    parser.add_argument("--provider", help="mock ou openai-compativel")
    args = parser.parse_args()

    if args.provider:
        import os

        os.environ["LLM_PROVIDER"] = args.provider

    requisicao = RequisicaoGeracao(
        uso_escolar=args.uso,
        codigo_ancora=args.codigo,
        observacoes=args.observacoes,
    )

    resultado = gerar_e_salvar(requisicao)
    print(f"Geração: {resultado['id']}")
    print(f"Provedor: {resultado['provedor']}")
    print(f"Plano:   {resultado['caminho_plano']}")
    print(f"Caderno: {resultado['caminho_caderno']}")
    print(f"Códigos: {', '.join(resultado['codigos'])}")
    if resultado["avisos"]:
        print("Avisos:")
        for aviso in resultado["avisos"]:
            print(f"  - {aviso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
