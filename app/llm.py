"""Clientes de geração em duas etapas: plano e atividades.

- ``MockLLM``: estrutural, sem custo, para testes e demonstração offline.
- ``OpenAICompativel``: OpenAI (ou endpoint compatível) para o material real.

O modelo escolhe códigos e escreve texto pedagógico. A descrição oficial da
BNCC nunca é escrita por ele: o resolvedor injeta o texto do CSV.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import httpx

from app.bncc import Habilidade, normalizar
from app.contract import (
    AtividadeGerada,
    Avaliacao,
    BrincadeiraCasa,
    CadernoAtividades,
    CadernoGerado,
    CampoExperienciaItem,
    CapaCaderno,
    ConteudoAtividade,
    HabilidadeSelecionada,
    Identificacao,
    IndicadorAvaliacao,
    ItemLegendaCor,
    Momento,
    NotaCoberturaGerada,
    ObjetivosAno,
    ParLigar,
    PlanoAula,
    PlanoGerado,
    Recurso,
    RelatorioVerificacao,
    SCHEMA_CADERNO,
    SCHEMA_PLANO,
    TIPOS_ATIVIDADE,
)

RAIZ = Path(__file__).resolve().parents[1]
PROMPT_PLANO = RAIZ / "prompts" / "system_plano.md"
PROMPT_ATIVIDADES = RAIZ / "prompts" / "system_atividades.md"
PROMPT_PLANO_EF = RAIZ / "prompts" / "system_plano_ef.md"
PROMPT_ATIVIDADES_EF = RAIZ / "prompts" / "system_atividades_ef.md"
PROMPT_VERIFICADOR = RAIZ / "prompts" / "verificador.md"
PROMPT_VERIFICADOR_EF = RAIZ / "prompts" / "verificador_ef.md"

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
    "Língua Portuguesa": "📚",
    "Arte": "🎨",
    "Educação Física": "🏃",
    "Ensino Religioso": "🤝",
    "Matemática": "🔢",
    "Ciências": "🔬",
    "Geografia": "🌍",
    "História": "🏛️",
}

FAIXAS_ETARIAS_EF = {
    "1º ano": "6 a 7 anos",
    "2º ano": "7 a 8 anos",
    "3º ano": "8 a 9 anos",
    "4º ano": "9 a 10 anos",
    "5º ano": "10 a 11 anos",
}

RECURSOS_GENERICOS = [
    ("📄", "Folhas impressas da atividade (uma por criança)."),
    ("✏️", "Lápis, borracha e apontador."),
    ("🖍️", "Lápis de cor, giz de cera e canetinhas de ponta grossa."),
    ("✂️", "Tesoura sem ponta e cola bastão."),
    ("🧩", "Material manipulável para a atividade principal."),
    ("📦", "Caixa ou saco surpresa para a dinâmica de abertura."),
    ("🎵", "Música curta para acolhida e encerramento."),
    ("🚩", "Cartaz ou mural para registrar as produções."),
]


class ErroLLM(RuntimeError):
    """Falha ao obter ou interpretar a resposta do provedor de IA."""


@dataclass
class RequisicaoGeracao:
    uso_escolar: str
    codigo_ancora: str
    observacoes: str = ""
    quantidade_atividades: int = 5


class LLMClient(Protocol):
    nome: str

    def gerar_plano(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
        feedback: list[str] | None = None,
    ) -> PlanoGerado: ...

    def gerar_atividades(
        self,
        plano: PlanoAula,
        schema: dict,
        feedback: list[str] | None = None,
        atribuicoes: list[dict] | None = None,
    ) -> CadernoGerado: ...

    def verificar_atividades(
        self,
        plano: PlanoAula,
        caderno: CadernoAtividades,
    ) -> RelatorioVerificacao: ...


# ---------------------------------------------------------------------------
# Mock estrutural
# ---------------------------------------------------------------------------


def _campos_de(
    candidatos: list[Habilidade],
    preencher_educacao_infantil: bool = True,
) -> list[CampoExperienciaItem]:
    vistos: set[str] = set()
    campos: list[CampoExperienciaItem] = []
    for habilidade in candidatos:
        if habilidade.sigla_campo in vistos:
            continue
        vistos.add(habilidade.sigla_campo)
        campos.append(
            CampoExperienciaItem(
                icone=ICONES_CAMPOS.get(habilidade.campo_experiencia, "✨"),
                nome=habilidade.campo_experiencia,
                justificativa=f"O tema dialoga com este campo ao trabalhar o objetivo oficial.",
            )
        )
        if len(campos) == 4:
            break
    if not preencher_educacao_infantil:
        return campos
    for nome in CAMPOS_OFICIAIS:
        if len(campos) == 4:
            break
        if nome not in {campo.nome for campo in campos}:
            campos.append(
                CampoExperienciaItem(
                    icone=ICONES_CAMPOS.get(nome, "✨"),
                    nome=nome,
                    justificativa="Campo articulado ao tema da aula.",
                )
            )
    return campos


def _objetivos_mock(ano_fundamental: str | None = None) -> list[ObjetivosAno]:
    if ano_fundamental:
        return [
            ObjetivosAno(
                ano=ano_fundamental,
                itens=[
                    "Reconhecer elementos da habilidade em situações do cotidiano.",
                    "Aplicar o que aprendeu em uma atividade prática.",
                    "Explicar com suas palavras o que descobriu.",
                    "Relacionar a habilidade a outras áreas do conhecimento.",
                    "Registrar o que aprendeu com apoio do professor.",
                    "Comparar exemplos e contraexemplos da habilidade.",
                    "Usar a habilidade em uma situação nova.",
                ],
            )
        ]
    return [
        ObjetivosAno(
            ano="Pré I",
            itens=[
                "Reconhecer elementos do objetivo oficial em situações do cotidiano.",
                "Explorar materiais e linguagens relacionados ao tema.",
                "Participar das atividades propostas com apoio do professor.",
                "Compartilhar descobertas com o grupo.",
            ],
        ),
        ObjetivosAno(
            ano="Pré II",
            itens=[
                "Representar o tema com mais autonomia.",
                "Comparar e registrar elementos do tema.",
                "Identificar semelhanças e diferenças.",
                "Explicar o que aprendeu com suas próprias palavras.",
            ],
        ),
    ]


class MockLLM:
    nome = "mock"

    def gerar_plano(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
        feedback: list[str] | None = None,
    ) -> PlanoGerado:
        ancora = next(
            (h for h in candidatos if h.codigo == requisicao.codigo_ancora),
            candidatos[0],
        )
        fundamental = requisicao.codigo_ancora.upper().startswith("EF")
        campos = _campos_de(
            candidatos,
            preencher_educacao_infantil=not fundamental,
        )
        objetivos = _objetivos_mock(requisicao.uso_escolar if fundamental else None)
        termo = "estudantes" if fundamental else "crianças"

        return PlanoGerado(
            titulo=(
                f"{ancora.codigo} — habilidade oficial"
                if fundamental
                else f"{ancora.codigo} — objetivo oficial"
            ),
            subtitulo=(
                f"Ensino Fundamental I • {requisicao.uso_escolar}"
                if fundamental
                else f"Educação Infantil • {requisicao.uso_escolar}"
            ),
            identificacao=Identificacao(
                tema=ancora.objetivo,
                codigo_ancora=ancora.codigo,
                turmas=[requisicao.uso_escolar],
                faixa_etaria=(
                    FAIXAS_ETARIAS_EF.get(requisicao.uso_escolar, "6 a 11 anos")
                    if fundamental
                    else "4 a 5 anos"
                ),
                tempo_estimado="50 minutos" if fundamental else "60 minutos",
                area_integradora=ancora.campo_experiencia,
            ),
            campos_experiencia=campos,
            objetivos=objetivos,
            habilidades=[
                HabilidadeSelecionada(codigo=habilidade.codigo)
                for habilidade in candidatos
            ],
            recursos=[
                Recurso(icone=icone, descricao=descricao)
                for icone, descricao in RECURSOS_GENERICOS
            ],
            desenvolvimento=[
                Momento(ordem=1, titulo="Acolhida", descricao=f"Receber os {termo} e apresentar a habilidade do dia.", minutos=5),
                Momento(ordem=2, titulo="Conversa inicial", descricao=f"Ouvir o que os {termo} já sabem sobre o tema.", minutos=8),
                Momento(ordem=3, titulo="Exploração da habilidade", descricao="Apresentar a habilidade oficial com apoio de material concreto.", minutos=10),
                Momento(ordem=4, titulo="Atividade principal", descricao="Realizar a atividade principal do caderno com mediação.", minutos=15),
                Momento(ordem=5, titulo="Prática orientada", descricao="Fazer uma prática relacionada à habilidade.", minutos=7),
                Momento(ordem=6, titulo="Registro", descricao=f"Registrar as produções e as falas dos {termo}.", minutos=6),
                Momento(ordem=7, titulo="Encerramento", descricao="Retomar a habilidade e conversar sobre o que aprenderam.", minutos=4),
            ],
            avaliacao=Avaliacao(
                introducao="A avaliação é processual e formativa; observe a participação e os registros.",
                indicadores=[
                    IndicadorAvaliacao(criterio="Reconhece o objetivo", pre_1="Com apoio", pre_2="Com autonomia"),
                    IndicadorAvaliacao(criterio="Participa da atividade", pre_1="Com incentivo", pre_2="Com iniciativa"),
                    IndicadorAvaliacao(criterio="Expressa o que aprendeu", pre_1="Com mediação", pre_2="Sozinho"),
                    IndicadorAvaliacao(criterio="Colabora com o grupo", pre_1="Com lembrete", pre_2="Espontaneamente"),
                ],
            ),
            adaptacoes=[
                f"Para {termo} com dificuldade motora, oferecer material maior e apoio físico.",
                f"Para {termo} com deficiência visual, usar materiais com textura e contraste.",
                f"Para {termo} tímidos, permitir resposta em pequenos grupos.",
                "Para turmas numerosas, dividir a atividade em estações.",
            ],
            observacoes_professor="",
            dica="Ajuste os tempos conforme a rotina da instituição e o ritmo da turma.",
            brincadeira_casa=BrincadeiraCasa(
                titulo="Levar o objetivo para casa",
                descricao="Convidar a família a conversar sobre o tema e registrar uma descoberta.",
                organizacao="Enviar uma folha simples para o registro da família.",
            ),
        )

    def gerar_atividades(
        self,
        plano: PlanoAula,
        schema: dict,
        feedback: list[str] | None = None,
        atribuicoes: list[dict] | None = None,
    ) -> CadernoGerado:
        codigos = [h.codigo for h in plano.habilidades]
        ancora = plano.identificacao.codigo_ancora
        if ancora in codigos:
            codigos.remove(ancora)
        codigos = [ancora] + codigos
        objetivos = [item for bloco in plano.objetivos for item in bloco.itens]

        if atribuicoes:
            escolhidos = [
                (item["codigo"], item["tipo"], item["objetivo_indice"])
                for item in atribuicoes
            ]
        else:
            escolhidos = [
                (
                    codigo,
                    TIPOS_ATIVIDADE[(indice - 1) % len(TIPOS_ATIVIDADE)],
                    (indice - 1) % len(objetivos) + 1,
                )
                for indice, codigo in enumerate(codigos[:5], start=1)
            ]

        atividades: list[AtividadeGerada] = []
        for indice, (codigo, tipo, objetivo_indice) in enumerate(escolhidos, start=1):
            conteudo, titulo, enunciado = self._conteudo_por_tipo(tipo, indice)
            atividades.append(
                AtividadeGerada(
                    numero=indice,
                    titulo=titulo,
                    enunciado=enunciado,
                    tipo=tipo,
                    codigo_bncc=codigo,
                    objetivo_indice=objetivo_indice,
                    objetivo_relacionado=objetivos[objetivo_indice - 1],
                    imagem_chave=self._imagem_chave(tipo),
                    imagem_alt=self._imagem_alt(tipo),
                    conteudo=conteudo,
                )
            )

        usados = {atividade.objetivo_relacionado for atividade in atividades}
        nao_trabalhados = [objetivo for objetivo in objetivos if objetivo not in usados]
        cobertos = {atividade.codigo_bncc for atividade in atividades}

        return CadernoGerado(
            capa=CapaCaderno(
                titulo=plano.titulo,
                subtitulo="Caderno de Atividades",
                etapa=(
                    "Ensino Fundamental — Anos Iniciais"
                    if ancora.upper().startswith("EF")
                    else "Educação Infantil"
                ),
                faixa_etaria=plano.identificacao.faixa_etaria,
                alinhamento_bncc="Alinhado à BNCC",
                codigo_ancora=ancora,
            ),
            atividades=atividades,
            nota_cobertura=NotaCoberturaGerada(
                objetivos_nao_trabalhados=nao_trabalhados,
                sugestoes_extras=[
                    f"Habilidade não trabalhada no caderno: {codigo}."
                    for codigo in codigos
                    if codigo not in cobertos
                ],
            ),
        )

    def verificar_atividades(
        self,
        plano: PlanoAula,
        caderno: CadernoAtividades,
    ) -> RelatorioVerificacao:
        return RelatorioVerificacao(ok=True)

    def _imagem_alt(self, tipo: str) -> str:
        if tipo in {"contar", "cobrir_palavra"}:
            return ""
        return {
            "ligar": "objetos da atividade para ligar",
            "colorir": "cena simples para colorir",
            "desenhar": "criança desenhando sobre o tema",
            "completar": "sequência de objetos da atividade",
            "labirinto": "caminho simples até a escola",
            "recortar_colar": "formas para recortar e colar",
        }.get(tipo, "ilustração do tema da aula")

    def _imagem_chave(self, tipo: str) -> str | None:
        return {
            "ligar": "bola",
            "contar": "bola",
            "colorir": "tinta",
            "desenhar": "lapis",
            "completar": "numero",
            "labirinto": "casa",
            "recortar_colar": "tesoura",
            "cobrir_palavra": "letra",
        }.get(tipo)

    def _conteudo_por_tipo(self, tipo: str, indice: int):
        if tipo == "cobrir_palavra":
            return (
                ConteudoAtividade(texto_para_cobrir="TEMA", linhas_escrita=2),
                "Vamos escrever!",
                "Cubra as letrinhas pontilhadas e escreva a palavra.",
            )
        if tipo == "ligar":
            return (
                ConteudoAtividade(
                    pares=[
                        ParLigar(palavra="ABACAXI", letra="A"),
                        ParLigar(palavra="BOLA", letra="B"),
                        ParLigar(palavra="CASA", letra="C"),
                        ParLigar(palavra="DADO", letra="D"),
                    ]
                ),
                "Ligue os pares",
                "Ligue cada desenho à letra com que o nome começa.",
            )
        if tipo == "contar":
            return (
                ConteudoAtividade(quantidade=5, icone_chave="bola"),
                "Vamos contar!",
                "Conte quantos objetos há e pinte a quantidade certa.",
            )
        if tipo == "colorir":
            return (
                ConteudoAtividade(
                    legenda_cores=[
                        ItemLegendaCor(numero=1, cor="Rosa"),
                        ItemLegendaCor(numero=2, cor="Amarelo"),
                        ItemLegendaCor(numero=3, cor="Azul"),
                        ItemLegendaCor(numero=4, cor="Verde"),
                    ]
                ),
                "Colorir por número",
                "Pinte cada espaço seguindo a cor de cada número.",
            )
        if tipo == "completar":
            return (
                ConteudoAtividade(sequencia=["1", "2", "3", "4", "5"], lacunas=1),
                "Complete a sequência",
                "Complete o que falta na sequência.",
            )
        if tipo == "desenhar":
            return (
                ConteudoAtividade(
                    frases=["O que eu mais gosto:", "Minha cor favorita é:", "O que eu aprendi:"]
                ),
                "Desenhe e conte",
                "Desenhe o que você aprendeu sobre o tema.",
            )
        if tipo == "labirinto":
            return (
                ConteudoAtividade(rotulo_inicio="início", rotulo_fim="chegada"),
                "O caminho",
                "Ajude a criança a chegar ao fim do caminho.",
            )
        return (
            ConteudoAtividade(itens_recortar=["círculo", "quadrado", "triângulo"]),
            "Recorte e cole",
            "Recorte as formas e cole no lugar certo.",
        )


# ---------------------------------------------------------------------------
# OpenAI / compatível
# ---------------------------------------------------------------------------


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


def _prompt_plano(requisicao: RequisicaoGeracao, candidatos: list[Habilidade]) -> str:
    lista = [
        {
            "indice": indice,
            "codigo": h.codigo,
            "campo_experiencia": h.campo_experiencia,
            "objetivo": h.objetivo,
        }
        for indice, h in enumerate(candidatos, start=1)
    ]
    fundamental = requisicao.codigo_ancora.upper().startswith("EF")
    regra_objetivos = (
        "No Fundamental I, `objetivos` deve ter 7 itens, na ordem dos códigos: "
        "item 1 = código 1, item 2 = código 2, ..., item 7 = código 7. Cada item "
        "deve usar o verbo e o objeto da habilidade oficial correspondente."
        if fundamental
        else
        "Na Educação Infantil, distribua 4 objetivos em Pré I (códigos 1 a 4) e "
        "4 em Pré II (códigos 5, 6, 7 e repita o código 1 com mais profundidade)."
    )
    return (
        "Pedido do professor:\n"
        f"- Turma: {requisicao.uso_escolar}\n"
        f"- Código âncora: {requisicao.codigo_ancora}\n"
        f"- Observações: {requisicao.observacoes or 'nenhuma'}\n\n"
        "Os 7 códigos candidatos (use somente estes; não invente códigos):\n"
        f"{json.dumps(lista, ensure_ascii=False, indent=2)}\n\n"
        f"{regra_objetivos}\n"
    )


def _prompt_atividades(
    plano: PlanoAula,
    atribuicoes: list[dict] | None = None,
) -> str:
    objetivos = []
    indice = 1
    for bloco in plano.objetivos:
        for texto in bloco.itens:
            objetivos.append({"indice": indice, "ano": bloco.ano, "texto": texto})
            indice += 1

    total_objetivos = sum(len(bloco.itens) for bloco in plano.objetivos)
    payload = {
        "codigo_ancora": plano.identificacao.codigo_ancora,
        "titulo": plano.titulo,
        "tema": plano.identificacao.tema,
        "turmas": plano.identificacao.turmas,
        "objetivos": objetivos,
        "habilidades": [
            {
                "codigo": h.codigo,
                "descricao_oficial": h.descricao,
                "campo": h.campo_experiencia,
            }
            for h in plano.habilidades
        ],
        "campos_experiencia": [{"nome": c.nome} for c in plano.campos_experiencia],
        "atribuicoes_obrigatorias": atribuicoes or [],
    }

    return (
        "Plano validado pelo professor:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Gere exatamente 5 atividades, com 5 códigos diferentes e 5 tipos "
        "diferentes. Use **exatamente** as combinações de código, tipo e "
        "objetivo_indice de `atribuicoes_obrigatorias`, na ordem dada. O código "
        "âncora precisa estar em pelo menos uma delas. "
        "Use apenas os códigos de `habilidades`. Para cada atividade, escolha o "
        "código cuja `descricao_oficial` combina com o tipo e o conteúdo; a "
        "atividade precisa exigir o desempenho do verbo da habilidade (escrever, "
        "ligar, contar, desenhar, recortar, movimentar etc.). Não use desenhar "
        "para habilidade de escrita/leitura; não use ligar de palavras para "
        "movimento. Preencha `objetivo_indice` com o índice do objetivo do plano "
        "que corresponde a esse código. Não copie a descrição da BNCC em "
        "`objetivo_relacionado`; o sistema usa o índice. Liste na nota o que não "
        f"foi trabalhado e o que é sugestão extra. Use índice de 1 a {total_objetivos}."
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
        self.model = model or os.getenv("LLM_MODEL") or "gpt-4o"
        if not self.api_key:
            raise ErroLLM("LLM_API_KEY não configurada.")

    def _chamar(
        self,
        system: str,
        user: str,
        schema: dict,
        modelo: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        payload = {
            "model": modelo or self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "material_bncc",
                    "schema": schema,
                    "strict": False,
                },
            },
        }
        cabecalhos = {"Authorization": f"Bearer {self.api_key}"}

        with httpx.Client(timeout=180) as cliente:
            for tentativa in range(2):
                resposta = cliente.post(
                    f"{self.base_url}/chat/completions",
                    headers=cabecalhos,
                    json=payload,
                )
                if resposta.status_code == 429 and tentativa == 0:
                    espera = int(resposta.headers.get("retry-after", "5"))
                    time.sleep(min(espera, 15))
                    continue
                if resposta.status_code >= 400 and "response_format" in resposta.text:
                    payload["response_format"] = {"type": "json_object"}
                    resposta = cliente.post(
                        f"{self.base_url}/chat/completions",
                        headers=cabecalhos,
                        json=payload,
                    )
                if resposta.status_code >= 400:
                    raise ErroLLM(f"Provedor retornou {resposta.status_code}: {resposta.text[:400]}")
                dados = resposta.json()
                try:
                    return dados["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as erro:
                    raise ErroLLM(f"Resposta inesperada do provedor: {dados}") from erro
        raise ErroLLM("Não foi possível obter resposta do provedor.")

    def gerar_plano(
        self,
        requisicao: RequisicaoGeracao,
        candidatos: list[Habilidade],
        schema: dict,
        feedback: list[str] | None = None,
    ) -> PlanoGerado:
        prompt = (
            PROMPT_PLANO_EF
            if requisicao.codigo_ancora.upper().startswith("EF")
            else PROMPT_PLANO
        )
        system = prompt.read_text(encoding="utf-8")
        user = _prompt_plano(requisicao, candidatos)
        if feedback:
            user += "\n\nCorrija os erros da tentativa anterior:\n- " + "\n- ".join(feedback)
        conteudo = self._chamar(
            system,
            user,
            schema,
            temperature=float(os.getenv("LLM_TEMPERATURE_PLANO") or "0.4"),
        )
        try:
            return PlanoGerado.model_validate_json(_extrair_json(conteudo))
        except Exception as erro:
            raise ErroLLM(f"Plano inválido devolvido pelo provedor: {erro}") from erro

    def gerar_atividades(
        self,
        plano: PlanoAula,
        schema: dict,
        feedback: list[str] | None = None,
        atribuicoes: list[dict] | None = None,
    ) -> CadernoGerado:
        prompt = (
            PROMPT_ATIVIDADES_EF
            if plano.identificacao.codigo_ancora.upper().startswith("EF")
            else PROMPT_ATIVIDADES
        )
        system = prompt.read_text(encoding="utf-8")
        user = _prompt_atividades(plano, atribuicoes=atribuicoes)
        if feedback:
            user += "\n\nCorrija os erros da tentativa anterior:\n- " + "\n- ".join(feedback)
        conteudo = self._chamar(
            system,
            user,
            schema,
            temperature=float(os.getenv("LLM_TEMPERATURE_ATIVIDADES") or "0.8"),
        )
        try:
            return CadernoGerado.model_validate_json(_extrair_json(conteudo))
        except Exception as erro:
            raise ErroLLM(f"Caderno inválido devolvido pelo provedor: {erro}") from erro

    def verificar_atividades(
        self,
        plano: PlanoAula,
        caderno: CadernoAtividades,
    ) -> RelatorioVerificacao:
        prompt = (
            PROMPT_VERIFICADOR_EF
            if plano.identificacao.codigo_ancora.upper().startswith("EF")
            else PROMPT_VERIFICADOR
        )
        system = prompt.read_text(encoding="utf-8")
        user = json.dumps(
            {
                "plano": plano.model_dump(mode="json"),
                "caderno": caderno.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
        schema = RelatorioVerificacao.model_json_schema()
        conteudo = self._chamar(
            system,
            user,
            schema,
            modelo=os.getenv("VERIFIER_MODEL") or "gpt-4o",
            temperature=0,
        )
        try:
            return RelatorioVerificacao.model_validate_json(_extrair_json(conteudo))
        except Exception as erro:
            raise ErroLLM(f"Relatório de verificação inválido: {erro}") from erro


def obter_cliente() -> LLMClient:
    provedor = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if provedor == "mock":
        return MockLLM()
    if not os.getenv("LLM_API_KEY"):
        raise ErroLLM(
            "LLM_PROVIDER está configurado, mas LLM_API_KEY não foi definida. "
            "Configure a chave ou use LLM_PROVIDER=mock explicitamente."
        )
    return OpenAICompativel()
