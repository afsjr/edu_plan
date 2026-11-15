"""Pipeline de geração: pedido → BNCC → IA → validação → documentos."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app import storage
from app.bncc import BaseBNCC
from app.config import carregar_env
from app.contract import SCHEMA_PADRAO, ErroContrato, Pacote, exportar_schema, resolver_pacote
from app.llm import LLMClient, RequisicaoGeracao, obter_cliente
from app.render_docx import render_plano
from app.render_pptx import render_caderno

carregar_env()


def gerar_pacote(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
    base: BaseBNCC | None = None,
) -> Pacote:
    base = base or BaseBNCC()
    cliente = cliente or obter_cliente()

    candidatos = base.candidatos_para(requisicao.uso_escolar)
    if not candidatos:
        raise ErroContrato(
            f"Não há habilidades candidatas para o uso escolar {requisicao.uso_escolar!r}."
        )

    if not SCHEMA_PADRAO.exists():
        exportar_schema(SCHEMA_PADRAO)
    schema = json.loads(SCHEMA_PADRAO.read_text(encoding="utf-8"))

    gerado = cliente.gerar_pacote(requisicao, candidatos, schema)
    permitidos = {habilidade.codigo for habilidade in candidatos}
    return resolver_pacote(gerado, base, permitidos)


def gerar_zip(
    requisicao: RequisicaoGeracao,
    cliente: LLMClient | None = None,
) -> bytes:
    """Gera o pacote e devolve um ZIP em memória, sem tocar no disco persistente."""
    cliente = cliente or obter_cliente()
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
        "tema": requisicao.tema,
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
    parser = argparse.ArgumentParser(description="Gera um pacote de plano + caderno.")
    parser.add_argument("--tema", required=True, help="Tema da aula")
    parser.add_argument("--uso", default="Pré II", help="Pré I, Pré II, Maternal ou Berçário")
    parser.add_argument("--observacoes", default="", help="Observações para a geração")
    parser.add_argument("--provider", help="mock ou openai-compativel (padrão: variável LLM_PROVIDER)")
    args = parser.parse_args()

    if args.provider:
        import os

        os.environ["LLM_PROVIDER"] = args.provider

    requisicao = RequisicaoGeracao(
        uso_escolar=args.uso,
        tema=args.tema,
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
