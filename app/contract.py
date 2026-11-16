"""Contrato do plano e do caderno.

O professor escolhe uma turma e um código âncora. O sistema seleciona mais 6
códigos da base, sempre em `data/bncc`, e gera o plano. Só depois da validação
do professor o caderno é gerado, a partir do plano.

O modelo de linguagem escreve o texto pedagógico e escolhe códigos. Ele nunca
escreve a descrição oficial da BNCC: ela é injetada a partir do CSV.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.bncc import BaseBNCC, normalizar

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
    objetivo_relacionado: str = Field(
        description="Objetivo do plano, copiado verbatim"
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


class Pacote(BaseModel):
    plano: PlanoAula
    caderno: CadernoAtividades
    avisos: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Resolução e validação
# ---------------------------------------------------------------------------


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


def _titulo_verbatim(descricao: str, limite: int = 70) -> str:
    texto = descricao.strip()
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0].rstrip(",.;:")
    return corte + "…"


def resolver_plano(
    gerado: PlanoGerado,
    base: BaseBNCC,
    permitidos: set[str] | None,
    ancora: str,
) -> PlanoAula:
    ancora_h = base.por_codigo(ancora)
    if ancora_h is None:
        raise CodigoBNCCInvalido(ancora, "identificacao.codigo_ancora", permitidos)

    habilidades = [
        _resolver_habilidade(item.codigo, base, permitidos, "plano.habilidades")
        for item in gerado.habilidades
    ]

    identificacao = gerado.identificacao.model_copy(
        update={
            "tema": ancora_h.objetivo,
            "codigo_ancora": ancora_h.codigo,
            "area_integradora": ancora_h.campo_experiencia,
        }
    )

    plano = PlanoAula(
        titulo=_titulo_verbatim(ancora_h.objetivo),
        subtitulo=gerado.subtitulo,
        identificacao=identificacao,
        campos_experiencia=gerado.campos_experiencia,
        objetivos=gerado.objetivos,
        habilidades=habilidades,
        recursos=gerado.recursos,
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
    plan_codes = {habilidade.codigo for habilidade in plano.habilidades}

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
                objetivo_relacionado=item.objetivo_relacionado,
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
