#!/usr/bin/env python3
"""Porta de qualidade para um pacote gerado (plano + caderno).

Uso:
    python3 scripts/validar_pacote.py storage/geracoes/<id>
    python3 scripts/validar_pacote.py storage/geracoes/<id> --comparar

O modo ``--comparar`` usa os modelos da instituição como referência de
estrutura (10 seções, 9 tabelas, 6 slides, 5 atividades).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docx import Document
from pptx import Presentation

RAIZ = Path(__file__).resolve().parents[1]
REF_DOCX = RAIZ / "exemplos base_inicial" / "Plano de Aula - Meu nome, minha identidade.docx"
REF_PPTX = RAIZ / "exemplos base_inicial" / "Atividades A4 ppt - Meu nome, minha identidade.pptx"


def _check(nome: str, ok: bool, detalhe: str = "") -> tuple[str, bool, str]:
    return (nome, ok, detalhe)


def validar(diretorio: Path, comparar: bool = False) -> int:
    pacote_path = diretorio / "pacote.json"
    docx_path = diretorio / "plano_aula.docx"
    pptx_path = diretorio / "caderno_atividades.pptx"

    for caminho in (pacote_path, docx_path, pptx_path):
        if not caminho.exists():
            print(f"Arquivo ausente: {caminho}", file=sys.stderr)
            return 1

    pacote = json.loads(pacote_path.read_text(encoding="utf-8"))
    plano = pacote["plano"]
    caderno = pacote["caderno"]
    fundamental = plano["identificacao"]["codigo_ancora"].upper().startswith("EF")

    objetivos = [item for bloco in plano["objetivos"] for item in bloco["itens"]]
    atividades = caderno["atividades"]
    codigos = [h["codigo"] for h in plano["habilidades"]]
    codigos_atividades = {a["codigo_bncc"] for a in atividades}
    tipos = {a["tipo"] for a in atividades}
    codigos_plano = set(codigos)

    checks = [
        _check("7 habilidades", len(codigos) == 7, f"{len(codigos)}"),
        _check(
            "4 componentes/campos",
            len({h["campo_experiencia"] for h in plano["habilidades"]}) == 4,
        ),
        _check("7 momentos", len(plano["desenvolvimento"]) == 7, f"{len(plano['desenvolvimento'])}"),
        _check("6 a 8 recursos", 6 <= len(plano["recursos"]) <= 8, f"{len(plano['recursos'])}"),
        _check("4 indicadores", len(plano["avaliacao"]["indicadores"]) == 4),
        _check("4 adaptações", len(plano["adaptacoes"]) == 4),
        _check(
            "objetivos (EF=7 / EI=7-8)",
            (len(objetivos) == 7) if fundamental else (7 <= len(objetivos) <= 8),
            f"{len(objetivos)}",
        ),
        _check("5 atividades", len(atividades) == 5, f"{len(atividades)}"),
        _check("5 códigos diferentes", len(codigos_atividades) == 5, f"{len(codigos_atividades)}"),
        _check("5 tipos diferentes", len(tipos) == 5, f"{len(tipos)}"),
        _check("âncora presente", plano["identificacao"]["codigo_ancora"] in codigos_atividades),
        _check("códigos no plano", codigos_atividades <= codigos_plano),
        _check("verificador sem avisos", not caderno.get("avisos_qualidade"), str(caderno.get("avisos_qualidade"))),
        _check(
            "objetivos das atividades no plano",
            all(a["objetivo_relacionado"] in objetivos for a in atividades),
        ),
    ]

    for atividade in atividades:
        conteudo = atividade["conteudo"]
        tipo = atividade["tipo"]
        required = {
            "cobrir_palavra": "texto_para_cobrir",
            "ligar": "pares",
            "contar": "quantidade",
            "colorir": "legenda_cores",
            "completar": "sequencia",
            "desenhar": "frases",
            "recortar_colar": "itens_recortar",
        }.get(tipo)
        if required:
            passa = bool(conteudo.get(required))
            checks.append(
                _check(
                    f"conteúdo da atividade {atividade['numero']}",
                    passa,
                    "" if passa else f"{tipo} sem {required}",
                )
            )

    documento = Document(docx_path)
    texto_docx = "\n".join(
        [paragrafo.text for paragrafo in documento.paragraphs]
        + [
            celula.text
            for tabela in documento.tables
            for linha in tabela.rows
            for celula in linha.cells
        ]
    )
    secoes = [
        "Identificação",
        "Objetivos de aprendizagem",
        "Habilidades da BNCC",
        "Recursos e materiais",
        "Desenvolvimento da aula",
        "Brincadeira & atividade para casa",
        "Avaliação",
        "Adaptações e acessibilidade",
        "Observações do(a) professor(a)",
    ]
    secoes.append("Componentes curriculares" if fundamental else "Campos de experiência")
    checks.append(
        _check(
            "10 seções no DOCX",
            all(secao in texto_docx for secao in secoes),
            ", ".join(secao for secao in secoes if secao not in texto_docx),
        )
    )
    checks.append(_check("DOCX com 8 a 10 tabelas", 8 <= len(documento.tables) <= 10, f"{len(documento.tables)}"))
    checks.append(_check("DOCX com 40+ parágrafos", len(documento.paragraphs) >= 40, f"{len(documento.paragraphs)}"))

    apresentacao = Presentation(pptx_path)
    imagens = sum(1 for slide in apresentacao.slides for shape in slide.shapes if shape.shape_type == 13)
    checks.append(_check("PPTX com 6 ou 7 slides", len(apresentacao.slides) in (6, 7), f"{len(apresentacao.slides)}"))
    checks.append(_check("PPTX com imagens", imagens > 0, f"{imagens} imagens"))

    falhas = [item for item in checks if not item[1]]
    largura = max(len(item[0]) for item in checks)
    for nome, ok, detalhe in checks:
        marca = "OK  " if ok else "FALHA"
        print(f"{marca}  {nome:<{largura}}  {detalhe}")

    if comparar and REF_DOCX.exists() and REF_PPTX.exists():
        ref_doc = Document(REF_DOCX)
        ref_ppt = Presentation(REF_PPTX)
        ref_imagens = sum(1 for slide in ref_ppt.slides for shape in slide.shapes if shape.shape_type == 13)
        ref_tabelas = len(ref_doc.tables) - (1 if fundamental else 0)
        print("\nComparação estrutural com o modelo:")
        print(f"  DOCX tabelas: {len(documento.tables)} / {ref_tabelas}")
        if fundamental:
            print("  (referência ajustada: Fund. I tem 1 bloco de objetivos, não 2)")
        print(f"  DOCX parágrafos: {len(documento.paragraphs)} / {len(ref_doc.paragraphs)}")
        print(f"  PPTX slides: {len(apresentacao.slides)} / {len(ref_ppt.slides)}")
        print(f"  PPTX imagens: {imagens} / {ref_imagens}")
        score = (
            (1 - abs(len(documento.tables) - ref_tabelas) / max(ref_tabelas, 1))
            + (1 - abs(len(documento.paragraphs) - len(ref_doc.paragraphs)) / max(len(ref_doc.paragraphs), 1))
            + (1 - abs(len(apresentacao.slides) - len(ref_ppt.slides)) / max(len(ref_ppt.slides), 1))
        ) / 3
        print(f"  Correspondência estrutural: {score * 100:.1f}%")

    print(f"\nResultado: {len(checks) - len(falhas)}/{len(checks)} verificações OK")
    return 1 if falhas else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida um pacote gerado.")
    parser.add_argument("diretorio", help="Pasta da geração em storage/geracoes/<id>")
    parser.add_argument("--comparar", action="store_true", help="Compara com os modelos da instituição")
    args = parser.parse_args()
    return validar(Path(args.diretorio), comparar=args.comparar)


if __name__ == "__main__":
    raise SystemExit(main())
