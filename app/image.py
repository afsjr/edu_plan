"""Geração de imagens em runtime com Cloudflare Workers AI (FLUX.1 Schnell).

A imagem é devolvida em base64 e embutida no JSON do caderno. Não há Blob nem
disco persistente. Sem chave configurada, o sistema usa apenas ícones/emoji.
"""

from __future__ import annotations

import os
import time

import httpx

from app.config import carregar_env

carregar_env()

MODELO_PADRAO = "@cf/black-forest-labs/flux-1-schnell"


class ErroImagem(RuntimeError):
    """Falha ao gerar ou interpretar a imagem."""


def disponivel() -> bool:
    return (
        (os.getenv("IMAGE_PROVIDER") or "").strip().lower() == "cloudflare"
        and bool(os.getenv("CLOUDFLARE_ACCOUNT_ID"))
        and bool(os.getenv("CLOUDFLARE_API_TOKEN"))
    )


def montar_prompt(descricao: str, tema: str) -> str:
    assunto = " ".join((descricao or tema).split()).strip()
    if not assunto:
        assunto = "elemento do tema da aula"
    return (
        f"flat vector illustration of {assunto}, single subject, centered, "
        "white background, thick clean outlines, solid pastel colors, "
        "children's textbook style, no text, no letters, no numbers, no watermark"
    )[:2048]


def gerar_imagem(prompt: str) -> str:
    """Chama o Cloudflare e devolve a imagem em base64."""
    if not disponivel():
        raise ErroImagem("Cloudflare não configurado (IMAGE_PROVIDER/chaves).")

    conta = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    modelo = (os.getenv("IMAGE_MODEL") or MODELO_PADRAO).strip()
    try:
        steps = int(os.getenv("IMAGE_STEPS") or "4")
    except ValueError:
        steps = 4
    steps = max(1, min(steps, 8))

    url = f"https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/{modelo}"
    payload = {"prompt": prompt, "steps": steps}
    dados: dict | None = None

    try:
        with httpx.Client(timeout=90) as cliente:
            for tentativa in range(2):
                resposta = cliente.post(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
                if resposta.status_code == 429 and tentativa == 0:
                    time.sleep(3)
                    continue
                if resposta.status_code >= 400:
                    raise ErroImagem(
                        f"Cloudflare retornou {resposta.status_code}: {resposta.text[:300]}"
                    )
                dados = resposta.json()
                break
    except httpx.HTTPError as erro:
        raise ErroImagem(f"Falha de rede no Cloudflare: {erro}") from erro

    if not dados or not dados.get("success"):
        raise ErroImagem(f"Cloudflare recusou a geração: {dados.get('errors')}")

    imagem = (dados.get("result") or {}).get("image")
    if not imagem or len(imagem) < 1000:
        raise ErroImagem("Cloudflare não retornou uma imagem válida.")
    return imagem
