"""Clientes de geração do pacote.

- ``MockLLM``: gera um pacote determinístico, sem custo e sem chave. Serve para
  o cliente testar o fluxo completo e para os testes automatizados.
- ``OpenAICompativel``: chama qualquer API compatível com o formato de chat
  completions da OpenAI (OpenAI, Gemini via endpoint compatível, etc.).

Trocar de provedor não muda o pipeline: ambos devolvem ``PacoteGerado``.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import httpx

from app.bncc import Habilidade, normalizar
from app.contract import (
    AtividadeGerada,
    BrincadeiraCasa,
    CadernoGerado,
    CampoExperienciaItem,
    CapaCaderno,
    ConteudoAtividade,
    HabilidadeSelecionada,
    Identificacao,
    ItemLegendaCor,
    Momento,
    ObjetivosAno,
    PacoteGerado,
    ParLigar,
    PlanoGerado,
    Recurso,
)
from app.exemplo_pacote import CODIGOS_PLANO, pacote_exemplo

RAIZ = Path(__file__).resolve().parents[1]
PROMPT_SISTEMA = RAIZ / "prompts" / "system.md"
SCHEMA = RAIZ / "prompts" / "schema_pacote.json"

CAMPOS_OFICIAIS = [
    "O eu, o outro e o nós",
    "Corpo, gestos e movimentos",
    "Traços, sons, cores e formas",
    "Escuta, fala, pensamento e imaginação",
    "Espaços, tempos, quantidades, relações e transformações",
]

ICONES_CAMPOS = {
    "O eu, o outro e o nós": "👥",
    "Corpo, gestos e movimentos": "🏃",
    "Traços, sons, cores e formas": "🎨",
    "Escuta, fala, pensamento e imaginação": "📚",
    "Espaços, tempos, quantidades, relações e transformações": "🔢",
}


class ErroLLM(RuntimeError):
    """Falha ao obter ou interpretar a resposta do provedor de IA."""


@dataclass
class RequisicaoGeracao:
    uso_escolar: str
    tema: str
    observacoes: str = ""
    quantidade_atividades: int = 5


class LLMClient(Protocol):
    nome: str

    def gerar_pacote(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
    ) -> PacoteGerado: ...


def _titulo(tema: str) -> str:
    return " ".join(palavra[:1].upper() + palavra[1:] for palavra in tema.strip().split())


def _primeira_palavra(tema: str) -> str:
    palavras = re.findall(r"[A-Za-zÀ-ÿ]{3,}", tema)
    if not palavras:
        return "NOME"
    return palavras[0].upper()[:8]


class MockLLM:
    """Gera um pacote plausível sem chamar nenhum serviço externo."""

    nome = "mock"

    def gerar_pacote(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
    ) -> PacoteGerado:
        permitidos = {habilidade.codigo for habilidade in candidatos}
        tema_normalizado = normalizar(requisicao.tema)

        if "nome" in tema_normalizado and "identidade" in tema_normalizado:
            if set(CODIGOS_PLANO).issubset(permitidos):
                pacote = pacote_exemplo()
                pacote.plano.titulo = _titulo(requisicao.tema)
                pacote.plano.identificacao.tema = _titulo(requisicao.tema)
                pacote.caderno.capa.titulo = _titulo(requisicao.tema)
                return pacote

        return self._generico(requisicao, candidatos)

    def _generico(self, requisicao: RequisicaoGeracao, candidatos: list[Habilidade]) -> PacoteGerado:
        tema = _titulo(requisicao.tema)
        faixa = "4 a 5 anos"
        turmas = ["Pré I (4 anos)", "Pré II (5 anos)"]

        campos: list[CampoExperienciaItem] = []
        vistos: set[str] = set()
        for habilidade in candidatos:
            if habilidade.sigla_campo in vistos:
                continue
            vistos.add(habilidade.sigla_campo)
            campos.append(
                CampoExperienciaItem(
                    icone=ICONES_CAMPOS.get(habilidade.campo_experiencia, "✨"),
                    nome=habilidade.campo_experiencia,
                    justificativa=f"O tema dialoga com este campo ao explorar {tema.lower()}.",
                )
            )
            if len(campos) == 4:
                break
        for nome in CAMPOS_OFICIAIS:
            if len(campos) == 4:
                break
            if nome not in {campo.nome for campo in campos}:
                campos.append(
                    CampoExperienciaItem(
                        icone=ICONES_CAMPOS.get(nome, "✨"),
                        nome=nome,
                        justificativa=f"O tema dialoga com este campo ao explorar {tema.lower()}.",
                    )
                )

        codigos = [habilidade.codigo for habilidade in candidatos]

        por_sigla: dict[str, list[str]] = {}
        for habilidade in candidatos:
            por_sigla.setdefault(habilidade.sigla_campo, []).append(habilidade.codigo)

        selecionados: list[str] = []
        indices = {sigla: 0 for sigla in por_sigla}
        while len(selecionados) < 7:
            avancou = False
            for sigla in por_sigla:
                if indices[sigla] < len(por_sigla[sigla]) and len(selecionados) < 7:
                    selecionados.append(por_sigla[sigla][indices[sigla]])
                    indices[sigla] += 1
                    avancou = True
            if not avancou:
                break
        habilidades = [HabilidadeSelecionada(codigo=codigo) for codigo in selecionados]

        def codigo_de(sigla: str, indice: int = 0) -> str:
            lista = por_sigla.get(sigla) or codigos
            return lista[indice % len(lista)]

        palavra = _primeira_palavra(requisicao.tema)
        atividades = [
            AtividadeGerada(
                numero=1,
                titulo="Vamos escrever!",
                enunciado=f"Cubra as letrinhas e escreva a palavra {palavra}.",
                tipo="cobrir_nome",
                codigo_bncc=codigo_de("EF", 0),
                conteudo=ConteudoAtividade(texto_para_cobrir=palavra, linhas_escrita=2),
            ),
            AtividadeGerada(
                numero=2,
                titulo="Eu e o tema",
                enunciado=f"Desenhe o que você mais gosta quando pensa em {tema.lower()}.",
                tipo="desenhar_rosto",
                codigo_bncc=codigo_de("EO", 0),
                conteudo=ConteudoAtividade(
                    frases=[
                        "O que eu mais gosto:",
                        "Minha cor favorita é:",
                        "A brincadeira que eu amo é:",
                        "O que eu aprendi hoje:",
                    ]
                ),
            ),
            AtividadeGerada(
                numero=3,
                titulo="A letra inicial",
                enunciado="Ligue cada desenho à letra com que o nome começa.",
                tipo="ligar_letra_inicial",
                codigo_bncc=codigo_de("EF", 1),
                conteudo=ConteudoAtividade(
                    pares=[
                        ParLigar(palavra="ABACAXI", letra="A"),
                        ParLigar(palavra="BOLA", letra="B"),
                        ParLigar(palavra="CASA", letra="C"),
                        ParLigar(palavra="DADO", letra="D"),
                    ]
                ),
            ),
            AtividadeGerada(
                numero=4,
                titulo="Colorir por número",
                enunciado="Pinte cada espaço seguindo a cor de cada número.",
                tipo="colorir_por_numero",
                codigo_bncc=codigo_de("TS", 0),
                conteudo=ConteudoAtividade(
                    legenda_cores=[
                        ItemLegendaCor(numero=1, cor="Rosa"),
                        ItemLegendaCor(numero=2, cor="Amarelo"),
                        ItemLegendaCor(numero=3, cor="Azul"),
                        ItemLegendaCor(numero=4, cor="Verde"),
                    ]
                ),
            ),
            AtividadeGerada(
                numero=5,
                titulo="O caminho",
                enunciado="Ajude a criança a chegar ao fim do caminho.",
                tipo="labirinto",
                codigo_bncc=codigo_de("CG", 0) if por_sigla.get("CG") else codigo_de("ET", 0),
                conteudo=ConteudoAtividade(rotulo_inicio="início", rotulo_fim="chegada"),
            ),
        ]

        return PacoteGerado(
            plano=PlanoGerado(
                titulo=tema,
                subtitulo=f"Educação Infantil • Pré I e Pré II • {faixa}",
                identificacao=Identificacao(
                    tema=tema,
                    turmas=turmas,
                    faixa_etaria=faixa,
                    tempo_estimado="60 minutos",
                    area_integradora=f"Tema integrador: {tema}",
                ),
                campos_experiencia=campos,
                objetivos=[
                    ObjetivosAno(
                        ano="Pré I",
                        itens=[
                            f"Reconhecer elementos do tema {tema.lower()}.",
                            "Explorar materiais e linguagens relacionados ao tema.",
                        ],
                    ),
                    ObjetivosAno(
                        ano="Pré II",
                        itens=[
                            f"Representar o tema {tema.lower()} com mais autonomia.",
                            "Comparar, contar e registrar elementos do tema.",
                        ],
                    ),
                ],
                habilidades=habilidades,
                recursos=[
                    Recurso(icone="🪪", descricao="Crachás e fichas com nomes."),
                    Recurso(icone="🎨", descricao="Lápis de cor, giz de cera e canetinhas."),
                    Recurso(icone="📄", descricao="Folhas do caderno de atividades."),
                    Recurso(icone="✂️", descricao="Cola bastão e recortes de papel colorido."),
                    Recurso(icone="🎵", descricao="Música e caixa surpresa."),
                    Recurso(icone="📦", descricao="Cartaz e materiais de apoio."),
                ],
                desenvolvimento=[
                    Momento(ordem=1, titulo="Acolhida", descricao="Receber as crianças chamando cada uma pelo nome.", minutos=5),
                    Momento(ordem=2, titulo="Dinâmica de abertura", descricao="Apresentar o tema com uma caixa surpresa.", minutos=8),
                    Momento(ordem=3, titulo="Roda de conversa", descricao="Ouvir as crianças e registrar as falas.", minutos=10),
                    Momento(ordem=4, titulo="Exploração do tema", descricao="Comparar materiais e levantar hipóteses.", minutos=7),
                    Momento(ordem=5, titulo="Atividade principal", descricao="Realizar as folhas do caderno com apoio do professor.", minutos=18),
                    Momento(ordem=6, titulo="Brincadeira", descricao="Fazer uma brincadeira cantada com o tema.", minutos=8),
                    Momento(ordem=7, titulo="Encerramento", descricao="Mostrar as produções e conversar sobre o que aprenderam.", minutos=4),
                ],
                dica="Ajuste os tempos conforme a rotina da turma e o ritmo das crianças.",
                brincadeira_casa=BrincadeiraCasa(
                    titulo="Levar o tema para casa",
                    descricao="Convidar a família a conversar sobre o tema e registrar uma descoberta.",
                    organizacao="Enviar uma folha simples para o registro da família.",
                ),
            ),
            caderno=CadernoGerado(
                capa=CapaCaderno(
                    titulo=tema,
                    subtitulo="Caderno de Atividades",
                    etapa="Educação Infantil",
                    faixa_etaria="Pré I e Pré II • 4 a 5 anos",
                    alinhamento_bncc="Alinhado à BNCC",
                ),
                atividades=atividades,
            ),
        )


def _extrair_json(texto: str) -> str:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-zA-Z]*\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio == -1 or fim == -1 or fim <= inicio:
        raise ErroLLM("A resposta não contém um objeto JSON.")
    return texto[inicio : fim + 1]


def _prompt_usuario(requisicao: RequisicaoGeracao, candidatos: list[Habilidade]) -> str:
    lista = [
        {
            "codigo": habilidade.codigo,
            "grupo_etario": habilidade.grupo_etario,
            "campo_experiencia": habilidade.campo_experiencia,
            "objetivo": habilidade.objetivo,
        }
        for habilidade in candidatos
    ]
    return (
        "Pedido do professor:\n"
        f"- Uso escolar: {requisicao.uso_escolar}\n"
        f"- Tema: {requisicao.tema}\n"
        f"- Observações: {requisicao.observacoes or 'nenhuma'}\n"
        f"- Quantidade de atividades: {requisicao.quantidade_atividades}\n\n"
        "Candidatos da BNCC (use somente estes códigos):\n"
        f"{json.dumps(lista, ensure_ascii=False, indent=2)}\n"
    )


class OpenAICompativel:
    """Cliente para APIs no formato chat completions da OpenAI."""

    nome = "openai-compativel"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        if not self.api_key:
            raise ErroLLM("LLM_API_KEY não configurada.")

    def gerar_pacote(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
    ) -> PacoteGerado:
        system = PROMPT_SISTEMA.read_text(encoding="utf-8")
        user = _prompt_usuario(requisicao, candidatos)

        payload = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "pacote_aula",
                    "schema": schema,
                    "strict": False,
                },
            },
        }

        cabecalhos = {"Authorization": f"Bearer {self.api_key}"}

        with httpx.Client(timeout=180) as cliente:
            resposta = cliente.post(
                f"{self.base_url}/chat/completions",
                headers=cabecalhos,
                json=payload,
            )
            if resposta.status_code >= 400 and "response_format" in resposta.text:
                payload["response_format"] = {"type": "json_object"}
                resposta = cliente.post(
                    f"{self.base_url}/chat/completions",
                    headers=cabecalhos,
                    json=payload,
                )
            if resposta.status_code >= 400:
                raise ErroLLM(f"Provedor de IA retornou {resposta.status_code}: {resposta.text[:400]}")

            dados = resposta.json()

        try:
            conteudo = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            raise ErroLLM(f"Resposta inesperada do provedor: {dados}") from erro

        try:
            return PacoteGerado.model_validate_json(_extrair_json(conteudo))
        except Exception as erro:
            raise ErroLLM(f"JSON inválido devolvido pelo provedor: {erro}") from erro


def obter_cliente() -> LLMClient:
    provedor = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if provedor == "mock" or not os.getenv("LLM_API_KEY"):
        return MockLLM()
    return OpenAICompativel()
