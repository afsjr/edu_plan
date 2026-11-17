"""Atribuição determinística de código, tipo e objetivo para as 5 atividades.

O modelo de linguagem escreve o texto, mas não escolhe livremente o tipo. A
atribuição abaixo reduz desalinhamentos: cada código recebe um tipo compatível
com o verbo da habilidade oficial, e cada atividade aponta para o objetivo do
plano mais próximo dessa habilidade.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from itertools import combinations, product

from app.bncc import normalizar
from app.contract import PlanoAula

TIPOS = [
    "cobrir_palavra",
    "ligar",
    "contar",
    "colorir",
    "completar",
    "desenhar",
    "labirinto",
    "recortar_colar",
]

SIGLAS_EI = {
    "O eu, o outro e o nós": "EO",
    "Corpo, gestos e movimentos": "CG",
    "Traços, sons, cores e formas": "TS",
    "Escuta, fala, pensamento e imaginação": "EF",
    "Espaços, tempos, quantidades, relações e transformações": "ET",
}

SIGLAS_EF = {
    "Língua Portuguesa": "LP",
    "Arte": "AR",
    "Educação Física": "EF",
    "Ensino Religioso": "ER",
    "Matemática": "MA",
    "Ciências": "CI",
    "Geografia": "GE",
    "História": "HI",
}

PREFERENCIAS = {
    # Educação Infantil
    "EO": ["desenhar", "recortar_colar", "labirinto"],
    "CG": ["labirinto", "recortar_colar", "desenhar"],
    "TS": ["colorir", "desenhar", "recortar_colar"],
    "EF_EI": ["cobrir_palavra", "ligar", "completar", "desenhar"],
    "ET": ["contar", "completar", "colorir"],
    # Ensino Fundamental I
    "LP": ["cobrir_palavra", "ligar", "completar", "desenhar"],
    "AR": ["colorir", "desenhar", "recortar_colar"],
    "EF_EF": ["labirinto", "recortar_colar", "desenhar"],
    "ER": ["desenhar", "recortar_colar", "completar"],
    "MA": ["contar", "completar", "colorir", "ligar"],
    "CI": ["desenhar", "labirinto", "completar", "recortar_colar"],
    "GE": ["desenhar", "labirinto", "completar"],
    "HI": ["desenhar", "completar", "recortar_colar"],
}


def _fundamental(plano: PlanoAula) -> bool:
    return plano.identificacao.codigo_ancora.upper().startswith("EF")


def _sigla(plano: PlanoAula, campo: str) -> str:
    if _fundamental(plano):
        sigla = SIGLAS_EF.get(campo, "")
        return "EF_EF" if sigla == "EF" else sigla
    sigla = SIGLAS_EI.get(campo, "")
    return "EF_EI" if sigla == "EF" else sigla


def _candidatos_de_tipo(descricao: str, sigla: str) -> list[str]:
    texto = normalizar(descricao)

    if any(palavra in texto for palavra in ("historia", "narrativa", "conto")):
        return ["completar", "desenhar", "cobrir_palavra", "ligar"]

    if any(palavra in texto for palavra in ("danca", "movimento", "corpo", "gesto")):
        if any(palavra in texto for palavra in ("coordenacao", "caminho", "equilibrio", "motor")):
            return ["labirinto", "recortar_colar", "desenhar"]
        return ["recortar_colar", "desenhar", "labirinto"]

    if any(palavra in texto for palavra in ("sentimento", "comunicar", "emoção", "emocao", "ideia")):
        return ["desenhar", "recortar_colar", "labirinto"]

    if any(palavra in texto for palavra in ("cor", "cores", "pintura", "arte", "forma", "artes")):
        return ["colorir", "desenhar", "recortar_colar"]

    if any(palavra in texto for palavra in ("contar", "contagem", "quantidade", "numero", "numero", "medida", "comparar")):
        return ["contar", "completar", "colorir"]

    if any(palavra in texto for palavra in ("escrever", "escrita", "ler", "leitura", "palavra", "hipotese", "texto")):
        if any(palavra in texto for palavra in ("produzir", "criar", "historia")):
            return ["completar", "cobrir_palavra", "ligar", "desenhar"]
        return ["cobrir_palavra", "ligar", "completar", "desenhar"]

    return PREFERENCIAS.get(sigla, ["desenhar", "completar", "recortar_colar", "ligar"])


def _escolher_tipo(candidatos: list[str], usados: set[str]) -> str | None:
    for tipo in candidatos:
        if tipo not in usados:
            return tipo
    return None


def _objetivos_achatados(plano: PlanoAula) -> list[str]:
    return [item for bloco in plano.objetivos for item in bloco.itens]


def _melhor_objetivo(descricao: str, objetivos: list[str], usados: set[int]) -> int:
    if not objetivos:
        return 1
    alvo = normalizar(descricao)
    ordenados = sorted(
        range(len(objetivos)),
        key=lambda indice: SequenceMatcher(
            None, alvo, normalizar(objetivos[indice])
        ).ratio(),
        reverse=True,
    )
    for indice in ordenados:
        if (indice + 1) not in usados:
            return indice + 1
    return ordenados[0] + 1


def montar_atribuicoes(plano: PlanoAula, total: int = 5) -> list[dict]:
    """Escolhe a melhor combinação de 5 códigos e 5 tipos distintos.

    A âncora é obrigatória. Para cada código, as preferências vêm do verbo da
    habilidade oficial. A combinação maximiza o encaixe de tipo e a diversidade
    de campos/componentes.
    """
    objetivos = _objetivos_achatados(plano)
    habilidades = list(plano.habilidades)
    ancora = plano.identificacao.codigo_ancora
    ancora_h = next((h for h in habilidades if h.codigo == ancora), habilidades[0])
    outros = [h for h in habilidades if h.codigo != ancora_h.codigo]

    def opcoes(h):
        sigla = _sigla(plano, h.campo_experiencia)
        tipos = _candidatos_de_tipo(h.descricao, sigla)
        # Remove duplicatas mantendo a ordem.
        vistos = set()
        return [t for t in tipos if not (t in vistos or vistos.add(t))]

    melhor = None
    for combo in combinations(outros, total - 1):
        grupo = [ancora_h] + list(combo)
        listas = [opcoes(h) for h in grupo]
        if any(not lista for lista in listas):
            continue
        for escolha in product(*listas):
            if len(set(escolha)) < total:
                continue
            encaixe = sum(max(0, 3 - listas[i].index(escolha[i])) for i in range(total))
            diversidade = len({h.campo_experiencia for h in grupo})
            score = encaixe * 10 + diversidade
            if melhor is None or score > melhor[0]:
                melhor = (score, grupo, escolha)

    if melhor is None:
        # Fallback: mantém a âncora e completa com os primeiros códigos/tipos.
        grupo = [ancora_h]
        usados_tipos: set[str] = set()
        for h in outros:
            if len(grupo) >= total:
                break
            lista = opcoes(h)
            tipo = next((t for t in lista if t not in usados_tipos), None)
            if tipo:
                grupo.append(h)
                usados_tipos.add(tipo)
        escolha = tuple(
            next((t for t in opcoes(h) if t not in set()), opcoes(h)[0])
            for h in grupo
        )
        melhor = (0, grupo, escolha)

    _, grupo, escolha = melhor
    # Âncora primeiro; demais na ordem original do plano.
    ordem = {h.codigo: i for i, h in enumerate(habilidades)}
    pares = list(zip(grupo, escolha))
    pares.sort(key=lambda par: (par[0].codigo != ancora_h.codigo, ordem.get(par[0].codigo, 99)))

    usados_objetivos: set[int] = set()
    atribuicoes = []
    for habilidade, tipo in pares[:total]:
        objetivo = _melhor_objetivo(habilidade.descricao, objetivos, usados_objetivos)
        usados_objetivos.add(objetivo)
        atribuicoes.append(
            {
                "codigo": habilidade.codigo,
                "tipo": tipo,
                "objetivo_indice": objetivo,
                "descricao_oficial": habilidade.descricao,
                "campo": habilidade.campo_experiencia,
            }
        )
    return atribuicoes
