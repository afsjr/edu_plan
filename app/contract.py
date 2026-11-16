"""Contrato do plano e do caderno.

O professor escolhe uma turma e um código âncora. O sistema seleciona mais 6
códigos da base, sempre em `data/bncc`, e gera o plano. Só depois da validação
do professor o caderno é gerado, a partir do plano.

O modelo de linguagem escreve o texto pedagógico e escolhe códigos. Ele nunca
escreve a descrição oficial da BNCC: ela é injetada a partir do CSV.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.bncc import BaseBNCC, normalizar
from app.icons import banco

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA_PLANO = RAIZ / "prompts" / "schema_plano.json"
SCHEMA_CADERNO = RAIZ / "prompts" / "schema_caderno.json"
SCHEMA_PACOTE = RAIZ / "prompts" / "schema_pacote.json"

TipoAtividade = Literal[
    "cobrir_palavra",
    "ligar",
    "contar",
    "colorir",
    "completar",
    "desenhar",
    "labirinto",
    "recortar_colar",
]

TIPOS_ATIVIDADE = [
    "cobrir_palavra",
    "ligar",
    "contar",
    "colorir",
    "completar",
    "desenhar",
    "labirinto",
    "recortar_colar",
]

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\ufffd\u25a1]")

ICONES_CAMPOS = {
    "O eu, o outro e o nós": "👥",
    "Corpo, gestos e movimentos": "🏃",
    "Traços, sons, cores e formas": "🎨",
    "Escuta, fala, pensamento e imaginação": "📚",
    "Espaços, tempos, quantidades, relações e transformações": "🔢",
}

ICONES_SEGUROS = {registro.emoji for registro in banco().registros()} | {
    "🪪",
    "📄",
    "✏️",
    "🖍️",
    "✂️",
    "🧩",
    "📦",
    "🎵",
    "🚩",
    "📚",
    "🧴",
    "📐",
    "🎒",
    "•",
    "✨",
}


def _icone_seguro(valor: str) -> str:
    valor = (valor or "").strip()
    if not valor or CJK_RE.search(valor):
        return "•"
    if valor in ICONES_SEGUROS:
        return valor
    icone = banco().obter(valor)
    if icone and icone.emoji:
        return icone.emoji
    return "•"


def _mapear_objetivo(texto: str, objetivos: list[str]) -> str:
    if not objetivos:
        raise ErroContrato("O plano não tem objetivos para relacionar.")
    alvo = normalizar(texto)
    for objetivo in objetivos:
        if normalizar(objetivo) == alvo:
            return objetivo
    melhor = max(
        objetivos,
        key=lambda objetivo: difflib.SequenceMatcher(
            None, alvo, normalizar(objetivo)
        ).ratio(),
    )
    similaridade = difflib.SequenceMatcher(None, alvo, normalizar(melhor)).ratio()
    if similaridade < 0.72:
        raise ErroContrato(
            f"Objetivo da atividade não pertence ao plano: {texto[:80]!r}"
        )
    return melhor


def _checar_portugues(valor: str, campo: str) -> None:
    if valor and CJK_RE.search(valor):
        raise ErroContrato(
            f"Texto fora do português do Brasil em {campo}: {valor[:80]!r}"
        )


def _validar_portugues_plano(gerado: PlanoGerado) -> None:
    _checar_portugues(gerado.titulo, "plano.titulo")
    _checar_portugues(gerado.subtitulo, "plano.subtitulo")
    for nome in (
        "tema",
        "faixa_etaria",
        "tempo_estimado",
        "area_integradora",
    ):
        _checar_portugues(
            getattr(gerado.identificacao, nome),
            f"plano.identificacao.{nome}",
        )
    for indice, campo in enumerate(gerado.campos_experiencia):
        _checar_portugues(campo.nome, f"plano.campos[{indice}].nome")
        _checar_portugues(
            campo.justificativa,
            f"plano.campos[{indice}].justificativa",
        )
    for bloco in gerado.objetivos:
        for item in bloco.itens:
            _checar_portugues(item, "plano.objetivos")
    for indice, recurso in enumerate(gerado.recursos):
        _checar_portugues(recurso.descricao, f"plano.recursos[{indice}]")
    for indice, momento in enumerate(gerado.desenvolvimento):
        _checar_portugues(momento.titulo, f"plano.desenvolvimento[{indice}].titulo")
        _checar_portugues(
            momento.descricao,
            f"plano.desenvolvimento[{indice}].descricao",
        )
    _checar_portugues(gerado.avaliacao.introducao, "plano.avaliacao.introducao")
    for indice, indicador in enumerate(gerado.avaliacao.indicadores):
        _checar_portugues(indicador.criterio, f"plano.avaliacao[{indice}].criterio")
        _checar_portugues(indicador.pre_1, f"plano.avaliacao[{indice}].pre_1")
        _checar_portugues(indicador.pre_2, f"plano.avaliacao[{indice}].pre_2")
    for indice, adaptacao in enumerate(gerado.adaptacoes):
        _checar_portugues(adaptacao, f"plano.adaptacoes[{indice}]")
    _checar_portugues(gerado.dica, "plano.dica")
    _checar_portugues(gerado.brincadeira_casa.titulo, "plano.brincadeira.titulo")
    _checar_portugues(gerado.brincadeira_casa.descricao, "plano.brincadeira.descricao")
    _checar_portugues(
        gerado.brincadeira_casa.organizacao,
        "plano.brincadeira.organizacao",
    )


def _validar_portugues_caderno(gerado: CadernoGerado) -> None:
    _checar_portugues(gerado.capa.titulo, "caderno.capa.titulo")
    _checar_portugues(gerado.capa.subtitulo, "caderno.capa.subtitulo")
    _checar_portugues(gerado.capa.etapa, "caderno.capa.etapa")
    _checar_portugues(gerado.capa.faixa_etaria, "caderno.capa.faixa_etaria")
    for indice, atividade in enumerate(gerado.atividades):
        _checar_portugues(atividade.titulo, f"caderno.atividades[{indice}].titulo")
        _checar_portugues(
            atividade.enunciado,
            f"caderno.atividades[{indice}].enunciado",
        )
        _checar_portugues(
            atividade.objetivo_relacionado,
            f"caderno.atividades[{indice}].objetivo",
        )
        _checar_portugues(
            atividade.imagem_alt,
            f"caderno.atividades[{indice}].imagem_alt",
        )
        if atividade.gabarito:
            _checar_portugues(atividade.gabarito, f"caderno.atividades[{indice}].gabarito")
        for frase in atividade.conteudo.frases:
            _checar_portugues(frase, f"caderno.atividades[{indice}].frases")
        for par in atividade.conteudo.pares:
            _checar_portugues(par.palavra, f"caderno.atividades[{indice}].pares")
    for objetivo in gerado.nota_cobertura.objetivos_nao_trabalhados:
        _checar_portugues(objetivo, "caderno.nota.objetivos")
    for sugestao in gerado.nota_cobertura.sugestoes_extras:
        _checar_portugues(sugestao, "caderno.nota.sugestoes")


class ErroContrato(ValueError):
    """Erro de estrutura ou de conteúdo no material gerado."""


class CodigoBNCCInvalido(ErroContrato):
    def __init__(self, codigo: str, contexto: str, permitidos: set[str] | None = None):
        detalhe = f"código BNCC inválido em {contexto}: {codigo!r}"
        if permitidos:
            detalhe += f" (permitidos: {', '.join(sorted(permitidos))})"
        super().__init__(detalhe)
        self.codigo = codigo
        self.contexto = contexto


# ---------------------------------------------------------------------------
# Plano
# ---------------------------------------------------------------------------


class Identificacao(BaseModel):
    tema: str = Field(description="Descrição oficial do código âncora, verbatim")
    codigo_ancora: str
    turmas: list[str] = Field(min_length=1)
    faixa_etaria: str
    tempo_estimado: str
    area_integradora: str = Field(description="Campo oficial do código âncora")


class CampoExperienciaItem(BaseModel):
    icone: str = Field(description="Um emoji curto, ex.: 👥")
    nome: str = Field(description="Nome oficial do campo de experiência")
    justificativa: str


class ObjetivosAno(BaseModel):
    ano: str = Field(description="Pré I ou Pré II")
    itens: list[str] = Field(min_length=2)


class HabilidadeSelecionada(BaseModel):
    codigo: str = Field(description="Código existente na lista de candidatos")


class Recurso(BaseModel):
    icone: str = Field(description="Um emoji curto, ex.: 🪪")
    descricao: str


class Momento(BaseModel):
    ordem: int = Field(ge=1, le=12)
    titulo: str
    descricao: str
    minutos: int = Field(ge=1, le=120)


class BrincadeiraCasa(BaseModel):
    titulo: str
    descricao: str
    organizacao: str = ""


class IndicadorAvaliacao(BaseModel):
    criterio: str
    pre_1: str
    pre_2: str


class Avaliacao(BaseModel):
    introducao: str
    indicadores: list[IndicadorAvaliacao] = Field(min_length=2)


class PlanoGerado(BaseModel):
    titulo: str
    subtitulo: str
    identificacao: Identificacao
    campos_experiencia: list[CampoExperienciaItem] = Field(min_length=1)
    objetivos: list[ObjetivosAno] = Field(min_length=1)
    habilidades: list[HabilidadeSelecionada] = Field(min_length=1)
    recursos: list[Recurso] = Field(min_length=1)
    desenvolvimento: list[Momento] = Field(min_length=1)
    avaliacao: Avaliacao
    adaptacoes: list[str] = Field(min_length=1)
    observacoes_professor: str = ""
    dica: str
    brincadeira_casa: BrincadeiraCasa

    @field_validator("desenvolvimento")
    @classmethod
    def ordenar_momentos(cls, momentos: list[Momento]) -> list[Momento]:
        return sorted(momentos, key=lambda momento: momento.ordem)


# ---------------------------------------------------------------------------
# Caderno
# ---------------------------------------------------------------------------


class ParLigar(BaseModel):
    palavra: str
    letra: str
    icone: str | None = None


class ItemLegendaCor(BaseModel):
    numero: int = Field(ge=1, le=20)
    cor: str


class ConteudoAtividade(BaseModel):
    texto_para_cobrir: str | None = None
    linhas_escrita: int | None = Field(default=None, ge=0, le=10)
    frases: list[str] = Field(default_factory=list)
    pares: list[ParLigar] = Field(default_factory=list)
    legenda_cores: list[ItemLegendaCor] = Field(default_factory=list)
    rotulo_inicio: str | None = None
    rotulo_fim: str | None = None
    quantidade: int | None = Field(default=None, ge=1, le=20)
    icone_chave: str | None = Field(
        default=None,
        description="Chave da biblioteca de ícones, ex.: abacaxi",
    )
    sequencia: list[str] = Field(default_factory=list)
    lacunas: int | None = Field(default=None, ge=1, le=10)
    itens_recortar: list[str] = Field(default_factory=list)
    elementos_extras: list[str] = Field(default_factory=list)


class AtividadeGerada(BaseModel):
    numero: int = Field(ge=1, le=10)
    titulo: str
    enunciado: str
    tipo: TipoAtividade
    codigo_bncc: str = Field(description="Código existente no plano")
    objetivo_indice: int = Field(
        ge=1,
        le=8,
        description="Índice do objetivo do plano (1 a 8)",
    )
    objetivo_relacionado: str = Field(
        default="",
        description="Objetivo do plano; o sistema também aceita o índice",
    )
    imagem_chave: str | None = Field(
        default=None,
        description="Chave opcional da biblioteca de ícones",
    )
    imagem_alt: str = Field(
        default="",
        description="Descrição curta, em português, da imagem que ilustraria a atividade",
    )
    conteudo: ConteudoAtividade = Field(default_factory=ConteudoAtividade)
    gabarito: str | None = None


class NotaCoberturaGerada(BaseModel):
    objetivos_nao_trabalhados: list[str] = Field(default_factory=list)
    sugestoes_extras: list[str] = Field(default_factory=list)


class CapaCaderno(BaseModel):
    titulo: str
    subtitulo: str
    etapa: str
    faixa_etaria: str
    alinhamento_bncc: str
    codigo_ancora: str


class CadernoGerado(BaseModel):
    capa: CapaCaderno
    atividades: list[AtividadeGerada] = Field(min_length=1)
    nota_cobertura: NotaCoberturaGerada = Field(default_factory=NotaCoberturaGerada)


class PacoteGerado(BaseModel):
    plano: PlanoGerado
    caderno: CadernoGerado


# ---------------------------------------------------------------------------
# Material resolvido (descrições oficiais injetadas)
# ---------------------------------------------------------------------------


class HabilidadeResolvida(BaseModel):
    codigo: str
    descricao: str
    campo_experiencia: str


class PlanoAula(BaseModel):
    titulo: str
    subtitulo: str
    identificacao: Identificacao
    campos_experiencia: list[CampoExperienciaItem]
    objetivos: list[ObjetivosAno]
    habilidades: list[HabilidadeResolvida]
    recursos: list[Recurso]
    desenvolvimento: list[Momento]
    avaliacao: Avaliacao
    adaptacoes: list[str]
    observacoes_professor: str
    dica: str
    brincadeira_casa: BrincadeiraCasa


class Atividade(BaseModel):
    numero: int
    titulo: str
    enunciado: str
    tipo: TipoAtividade
    codigo_bncc: str
    campo_experiencia: str
    descricao_bncc: str
    objetivo_relacionado: str
    imagem_chave: str | None = None
    imagem_alt: str = ""
    imagem_base64: str | None = None
    conteudo: ConteudoAtividade
    gabarito: str | None = None


class CodigoNaoTrabalhado(BaseModel):
    codigo: str
    descricao: str


class NotaCobertura(BaseModel):
    codigos_nao_trabalhados: list[CodigoNaoTrabalhado] = Field(default_factory=list)
    objetivos_nao_trabalhados: list[str] = Field(default_factory=list)
    sugestoes_extras: list[str] = Field(default_factory=list)


class CadernoAtividades(BaseModel):
    capa: CapaCaderno
    atividades: list[Atividade]
    nota_cobertura: NotaCobertura = Field(default_factory=NotaCobertura)
    imagem_status: str = ""
    avisos_qualidade: list[str] = Field(default_factory=list)


class Pacote(BaseModel):
    plano: PlanoAula
    caderno: CadernoAtividades
    avisos: list[str] = Field(default_factory=list)


class ProblemaAtividade(BaseModel):
    atividade: int
    motivo: str


class RelatorioVerificacao(BaseModel):
    ok: bool
    problemas: list[ProblemaAtividade] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Resolução e validação
# ---------------------------------------------------------------------------


def _resolver_objetivo(item: AtividadeGerada, objetivos: list[str]) -> str:
    if item.objetivo_indice and 1 <= item.objetivo_indice <= len(objetivos):
        return objetivos[item.objetivo_indice - 1]
    return _mapear_objetivo(item.objetivo_relacionado, objetivos)


def _resolver_habilidade(
    codigo: str,
    base: BaseBNCC,
    permitidos: set[str] | None,
    contexto: str,
) -> HabilidadeResolvida:
    habilidade = base.por_codigo(codigo)
    if habilidade is None:
        raise CodigoBNCCInvalido(codigo, contexto, permitidos)
    if permitidos is not None and habilidade.codigo not in permitidos:
        raise CodigoBNCCInvalido(codigo, contexto, permitidos)
    return HabilidadeResolvida(
        codigo=habilidade.codigo,
        descricao=habilidade.objetivo,
        campo_experiencia=habilidade.campo_experiencia,
    )


STOPWORDS_FINAIS = {
    "de", "da", "do", "das", "dos", "para", "por", "com", "sem", "e", "ou",
    "que", "em", "no", "na", "nos", "nas", "o", "a", "os", "as", "ao", "aos",
}


def _titulo_curto(descricao: str, minimo: int = 30, maximo: int = 95) -> str:
    """Trecho curto e completo da descrição oficial, sem reticências."""
    texto = " ".join(descricao.split()).strip()
    if not texto:
        return texto

    partes = re.split(r"[,;]", texto)
    acumulado = ""
    escolhido = ""
    for parte in partes:
        parte = parte.strip().strip(". ")
        if not parte:
            continue
        acumulado = f"{acumulado}, {parte}" if acumulado else parte
        if len(acumulado) < minimo:
            continue
        if acumulado.split()[-1].lower() in STOPWORDS_FINAIS:
            continue
        escolhido = acumulado
        break

    if not escolhido:
        ponto = texto.find(".")
        if 0 < ponto <= maximo:
            escolhido = texto[:ponto].strip()
    if not escolhido:
        escolhido = texto

    return escolhido


def resolver_plano(
    gerado: PlanoGerado,
    base: BaseBNCC,
    permitidos: set[str] | None,
    ancora: str,
) -> PlanoAula:
    ancora_h = base.por_codigo(ancora)
    if ancora_h is None:
        raise CodigoBNCCInvalido(ancora, "identificacao.codigo_ancora", permitidos)

    _validar_portugues_plano(gerado)

    habilidades = [
        _resolver_habilidade(item.codigo, base, permitidos, "plano.habilidades")
        for item in gerado.habilidades
    ]

    campos = [
        campo.model_copy(update={"icone": ICONES_CAMPOS.get(campo.nome, "•")})
        for campo in gerado.campos_experiencia
    ]
    recursos = [
        recurso.model_copy(update={"icone": _icone_seguro(recurso.icone)})
        for recurso in gerado.recursos
    ]

    identificacao = gerado.identificacao.model_copy(
        update={
            "tema": ancora_h.objetivo,
            "codigo_ancora": ancora_h.codigo,
            "area_integradora": ancora_h.campo_experiencia,
        }
    )

    plano = PlanoAula(
        titulo=_titulo_curto(ancora_h.objetivo),
        subtitulo=gerado.subtitulo,
        identificacao=identificacao,
        campos_experiencia=campos,
        objetivos=gerado.objetivos,
        habilidades=habilidades,
        recursos=recursos,
        desenvolvimento=gerado.desenvolvimento,
        avaliacao=gerado.avaliacao,
        adaptacoes=gerado.adaptacoes,
        observacoes_professor=gerado.observacoes_professor,
        dica=gerado.dica,
        brincadeira_casa=gerado.brincadeira_casa,
    )

    avisos = validar_plano(plano)
    if avisos:
        # avisos não impedem a renderização; ficam registrados no pacote
        pass
    return plano


def resolver_caderno(
    gerado: CadernoGerado,
    plano: PlanoAula,
    base: BaseBNCC,
) -> CadernoAtividades:
    _validar_portugues_caderno(gerado)

    plan_codes = {habilidade.codigo for habilidade in plano.habilidades}
    objetivos_plano = [item for bloco in plano.objetivos for item in bloco.itens]

    atividades: list[Atividade] = []
    for item in gerado.atividades:
        if item.codigo_bncc not in plan_codes:
            raise ErroContrato(
                f"A atividade {item.numero} usa {item.codigo_bncc}, que não está no plano."
            )
        resolvida = _resolver_habilidade(item.codigo_bncc, base, plan_codes, "caderno.atividades")
        atividades.append(
            Atividade(
                numero=item.numero,
                titulo=item.titulo,
                enunciado=item.enunciado,
                tipo=item.tipo,
                codigo_bncc=resolvida.codigo,
                campo_experiencia=resolvida.campo_experiencia,
                descricao_bncc=resolvida.descricao,
                objetivo_relacionado=_resolver_objetivo(item, objetivos_plano),
                imagem_chave=item.imagem_chave,
                imagem_alt=item.imagem_alt,
                conteudo=item.conteudo,
                gabarito=item.gabarito,
            )
        )

    atividade_codes = {atividade.codigo_bncc for atividade in atividades}
    codigos_nao_trabalhados = [
        CodigoNaoTrabalhado(codigo=habilidade.codigo, descricao=habilidade.descricao)
        for habilidade in plano.habilidades
        if habilidade.codigo not in atividade_codes
    ]

    nota = NotaCobertura(
        codigos_nao_trabalhados=codigos_nao_trabalhados,
        objetivos_nao_trabalhados=gerado.nota_cobertura.objetivos_nao_trabalhados,
        sugestoes_extras=gerado.nota_cobertura.sugestoes_extras,
    )

    capa = gerado.capa.model_copy(
        update={
            "titulo": plano.titulo,
            "subtitulo": "Caderno de Atividades",
            "etapa": "Educação Infantil",
            "faixa_etaria": plano.identificacao.faixa_etaria,
            "alinhamento_bncc": "Alinhado à BNCC",
            "codigo_ancora": plano.identificacao.codigo_ancora,
        }
    )

    caderno = CadernoAtividades(capa=capa, atividades=atividades, nota_cobertura=nota)
    validar_caderno(caderno, plano)
    return caderno


def resolver_pacote(
    gerado: PacoteGerado,
    base: BaseBNCC,
    permitidos: set[str] | None = None,
) -> Pacote:
    ancora = gerado.plano.identificacao.codigo_ancora
    plano = resolver_plano(gerado.plano, base, permitidos, ancora)
    caderno = resolver_caderno(gerado.caderno, plano, base)
    return Pacote(plano=plano, caderno=caderno, avisos=validar_plano(plano))


def validar_plano(plano: PlanoAula) -> list[str]:
    avisos: list[str] = []
    if len(plano.habilidades) != 7:
        avisos.append(f"O plano tem {len(plano.habilidades)} habilidades; o modelo usa 7.")
    if len({h.campo_experiencia for h in plano.habilidades}) != 4:
        avisos.append("O plano não cobre exatamente 4 campos de experiência.")
    if len(plano.campos_experiencia) != 4:
        avisos.append(f"O plano tem {len(plano.campos_experiencia)} campos; o modelo usa 4.")
    if not (6 <= len(plano.recursos) <= 8):
        avisos.append(f"O plano tem {len(plano.recursos)} recursos; o esperado é 6 a 8.")
    if len(plano.desenvolvimento) != 7:
        avisos.append(f"O plano tem {len(plano.desenvolvimento)} momentos; o modelo usa 7.")
    if len(plano.objetivos) != 2:
        avisos.append("O plano deve separar objetivos em Pré I e Pré II.")
    if not plano.avaliacao.indicadores:
        avisos.append("A seção de avaliação está sem indicadores.")
    if not plano.adaptacoes:
        avisos.append("A seção de adaptações está vazia.")
    return avisos


def validar_caderno(caderno: CadernoAtividades, plano: PlanoAula) -> None:
    if len(caderno.atividades) != 5:
        raise ErroContrato(
            f"O caderno deve ter exatamente 5 atividades; vieram {len(caderno.atividades)}."
        )
    numeros = [atividade.numero for atividade in caderno.atividades]
    if numeros != list(range(1, len(numeros) + 1)):
        raise ErroContrato(f"Atividades fora de ordem: {numeros}")

    plan_codes = {habilidade.codigo for habilidade in plano.habilidades}
    atividade_codes = {atividade.codigo_bncc for atividade in caderno.atividades}
    if not atividade_codes <= plan_codes:
        raise ErroContrato("Há atividade com código que não está no plano.")
    if plano.identificacao.codigo_ancora not in atividade_codes:
        raise ErroContrato("O código âncora precisa estar em pelo menos uma atividade.")

    objetivos = {normalizar(item) for bloco in plano.objetivos for item in bloco.itens}
    for atividade in caderno.atividades:
        if normalizar(atividade.objetivo_relacionado) not in objetivos:
            raise ErroContrato(
                f"A atividade {atividade.numero} aponta um objetivo que não está no plano."
            )


def exportar_schema(destino: Path = SCHEMA_PACOTE) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(PacoteGerado.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destino


def exportar_schemas() -> tuple[Path, Path]:
    SCHEMA_PLANO.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA_PLANO.write_text(
        json.dumps(PlanoGerado.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    SCHEMA_CADERNO.write_text(
        json.dumps(CadernoGerado.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return SCHEMA_PLANO, SCHEMA_CADERNO


if __name__ == "__main__":
    plano, caderno = exportar_schemas()
    pacote = exportar_schema()
    print(f"Schema do plano:   {plano}")
    print(f"Schema do caderno: {caderno}")
    print(f"Schema do pacote:  {pacote}")
