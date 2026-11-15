"""Contrato de saída do pacote (plano de aula + caderno de atividades).

Há dois níveis:

1. ``PacoteGerado`` — o que o modelo de linguagem devolve. Ele só *escolhe*
   códigos da BNCC; não escreve a descrição oficial.
2. ``Pacote`` — o que o sistema monta depois de resolver cada código na base
   oficial. A descrição e o campo de experiência vêm do CSV, nunca do LLM.

Essa separação é o que impede código inventado e paráfrase da BNCC.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.bncc import BaseBNCC, normalizar

RAIZ = Path(__file__).resolve().parents[1]
SCHEMA_PADRAO = RAIZ / "prompts" / "schema_pacote.json"

TipoAtividade = Literal[
    "cobrir_nome",
    "desenhar_rosto",
    "ligar_letra_inicial",
    "colorir_por_numero",
    "labirinto",
    "outro",
]


class ErroContrato(ValueError):
    """Erro de estrutura ou de conteúdo no pacote gerado."""


class CodigoBNCCInvalido(ErroContrato):
    def __init__(self, codigo: str, contexto: str, permitidos: set[str] | None = None):
        detalhe = f"código BNCC inválido em {contexto}: {codigo!r}"
        if permitidos:
            detalhe += f" (permitidos: {', '.join(sorted(permitidos))})"
        super().__init__(detalhe)
        self.codigo = codigo
        self.contexto = contexto


# ---------------------------------------------------------------------------
# O que o modelo de linguagem devolve
# ---------------------------------------------------------------------------


class Identificacao(BaseModel):
    tema: str
    turmas: list[str] = Field(min_length=1)
    faixa_etaria: str
    tempo_estimado: str
    area_integradora: str


class CampoExperienciaItem(BaseModel):
    icone: str = Field(description="Um emoji curto, ex.: 👥")
    nome: str
    justificativa: str


class ObjetivosAno(BaseModel):
    ano: str = Field(description="Pré I ou Pré II")
    itens: list[str] = Field(min_length=1)


class HabilidadeSelecionada(BaseModel):
    codigo: str = Field(description="Código existente na lista de candidatos, ex.: EI03EF01")


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


class PlanoGerado(BaseModel):
    titulo: str
    subtitulo: str
    identificacao: Identificacao
    campos_experiencia: list[CampoExperienciaItem] = Field(min_length=1)
    objetivos: list[ObjetivosAno] = Field(min_length=1)
    habilidades: list[HabilidadeSelecionada] = Field(min_length=1)
    recursos: list[Recurso] = Field(min_length=1)
    desenvolvimento: list[Momento] = Field(min_length=1)
    dica: str
    brincadeira_casa: BrincadeiraCasa

    @field_validator("desenvolvimento")
    @classmethod
    def ordenar_momentos(cls, momentos: list[Momento]) -> list[Momento]:
        return sorted(momentos, key=lambda momento: momento.ordem)


class ParLigar(BaseModel):
    palavra: str
    letra: str
    icone: str | None = Field(
        default=None,
        description="Chave opcional da biblioteca de ícones; o sistema também tenta pela palavra.",
    )


class ItemLegendaCor(BaseModel):
    numero: int = Field(ge=1, le=20)
    cor: str


class ConteudoAtividade(BaseModel):
    """Conteúdo específico de cada tipo de atividade.

    Nem todo campo é usado em todo tipo. O renderizador escolhe os campos
    conforme ``AtividadeGerada.tipo``.
    """

    texto_para_cobrir: str | None = Field(
        default=None, description="Nome ou palavra para cobrir, no tipo cobrir_nome"
    )
    linhas_escrita: int | None = Field(default=None, ge=0, le=10)
    frases: list[str] = Field(default_factory=list)
    pares: list[ParLigar] = Field(default_factory=list)
    legenda_cores: list[ItemLegendaCor] = Field(default_factory=list)
    rotulo_inicio: str | None = None
    rotulo_fim: str | None = None
    elementos_extras: list[str] = Field(default_factory=list)


class AtividadeGerada(BaseModel):
    numero: int = Field(ge=1, le=10)
    titulo: str
    enunciado: str
    tipo: TipoAtividade
    codigo_bncc: str = Field(description="Código existente na lista de candidatos")
    conteudo: ConteudoAtividade = Field(default_factory=ConteudoAtividade)
    gabarito: str | None = None


class CapaCaderno(BaseModel):
    titulo: str
    subtitulo: str
    etapa: str
    faixa_etaria: str
    alinhamento_bncc: str


class CadernoGerado(BaseModel):
    capa: CapaCaderno
    atividades: list[AtividadeGerada] = Field(min_length=1)


class PacoteGerado(BaseModel):
    plano: PlanoGerado
    caderno: CadernoGerado


# ---------------------------------------------------------------------------
# O que o sistema monta depois de validar os códigos
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
    conteudo: ConteudoAtividade
    gabarito: str | None = None


class CadernoAtividades(BaseModel):
    capa: CapaCaderno
    atividades: list[Atividade]


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


def resolver_pacote(
    gerado: PacoteGerado,
    base: BaseBNCC,
    permitidos: set[str] | None = None,
) -> Pacote:
    """Troca cada código escolhido pelo registro oficial da BNCC.

    ``permitidos`` restringe os códigos ao grupo/uso escolar do pedido. Se um
    código não existir ou não estiver na lista, levanta ``CodigoBNCCInvalido``.
    """
    habilidades = [
        _resolver_habilidade(item.codigo, base, permitidos, "plano.habilidades")
        for item in gerado.plano.habilidades
    ]

    atividades: list[Atividade] = []
    for item in gerado.caderno.atividades:
        resolvida = _resolver_habilidade(item.codigo_bncc, base, permitidos, "caderno.atividades")
        atividades.append(
            Atividade(
                numero=item.numero,
                titulo=item.titulo,
                enunciado=item.enunciado,
                tipo=item.tipo,
                codigo_bncc=resolvida.codigo,
                campo_experiencia=resolvida.campo_experiencia,
                descricao_bncc=resolvida.descricao,
                conteudo=item.conteudo,
                gabarito=item.gabarito,
            )
        )

    plano = PlanoAula(
        titulo=gerado.plano.titulo,
        subtitulo=gerado.plano.subtitulo,
        identificacao=gerado.plano.identificacao,
        campos_experiencia=gerado.plano.campos_experiencia,
        objetivos=gerado.plano.objetivos,
        habilidades=habilidades,
        recursos=gerado.plano.recursos,
        desenvolvimento=gerado.plano.desenvolvimento,
        dica=gerado.plano.dica,
        brincadeira_casa=gerado.plano.brincadeira_casa,
    )

    caderno = CadernoAtividades(capa=gerado.caderno.capa, atividades=atividades)

    avisos = validar_pacote(plano, caderno)
    return Pacote(plano=plano, caderno=caderno, avisos=avisos)


def validar_pacote(plano: PlanoAula, caderno: CadernoAtividades) -> list[str]:
    """Valida a forma do pacote. Erros estruturais impedem a renderização."""
    avisos: list[str] = []

    if len(caderno.atividades) != 5:
        raise ErroContrato(f"O MVP exige exatamente 5 atividades; vieram {len(caderno.atividades)}.")

    numeros = [atividade.numero for atividade in caderno.atividades]
    if numeros != list(range(1, len(numeros) + 1)):
        raise ErroContrato(f"Atividades fora de ordem: {numeros}")

    if len(plano.campos_experiencia) != 4:
        avisos.append(
            f"O plano tem {len(plano.campos_experiencia)} campos de experiência; o modelo usa 4."
        )

    if not (5 <= len(plano.desenvolvimento) <= 8):
        avisos.append(
            f"O plano tem {len(plano.desenvolvimento)} momentos; o esperado é de 5 a 8."
        )

    if not (4 <= len(plano.habilidades) <= 8):
        avisos.append(
            f"O plano tem {len(plano.habilidades)} habilidades; o esperado é de 4 a 8."
        )

    if len(plano.objetivos) != 2:
        avisos.append(
            f"O plano tem {len(plano.objetivos)} blocos de objetivos; o modelo separa Pré I e Pré II."
        )
    else:
        anos = {normalizar(objetivo.ano) for objetivo in plano.objetivos}
        if not anos & {"pre i", "pre 1"}:
            avisos.append("Não há bloco de objetivos identificado como Pré I.")
        if not anos & {"pre ii", "pre 2"}:
            avisos.append("Não há bloco de objetivos identificado como Pré II.")

    if len(caderno.atividades) != len({atividade.titulo for atividade in caderno.atividades}):
        avisos.append("Há atividades com títulos repetidos.")

    return avisos


def exportar_schema(destino: Path = SCHEMA_PADRAO) -> Path:
    """Escreve o JSON Schema do que o LLM deve devolver."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    schema: dict[str, Any] = PacoteGerado.model_json_schema()
    destino.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino


if __name__ == "__main__":
    caminho = exportar_schema()
    print(f"Schema exportado: {caminho}")
