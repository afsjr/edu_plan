"""Consulta local à base da BNCC do Ensino Fundamental — Anos Iniciais.

A base tem 574 habilidades (1º ao 5º ano), incluindo os ciclos multi-ano de
Arte (EF15AR) e Educação Física (EF12EF/EF35EF). A consulta é determinística e
em memória; para volume maior, a mesma interface pode ir para Postgres/pgvector.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from app.bncc import normalizar

RAIZ = Path(__file__).resolve().parents[1]
CSV_PADRAO = RAIZ / "data" / "bncc" / "bncc_ef.csv"

COMPONENTES = {
    "LP": "Língua Portuguesa",
    "AR": "Arte",
    "EF": "Educação Física",
    "ER": "Ensino Religioso",
    "MA": "Matemática",
    "CI": "Ciências",
    "GE": "Geografia",
    "HI": "História",
}

ANOS_POR_CICLO = {
    "01": {1},
    "02": {2},
    "03": {3},
    "04": {4},
    "05": {5},
    "12": {1, 2},
    "15": {1, 2, 3, 4, 5},
    "35": {3, 4, 5},
}


class CodigoNaoEncontrado(ValueError):
    """O código não existe na base ou não pertence ao ano solicitado."""


@dataclass(frozen=True)
class HabilidadeEF:
    ordem: int
    codigo: str
    etapa: str
    ano: str
    ciclo: str
    componente: str
    sigla_componente: str
    habilidade: str
    palavras_chave: str
    pagina_pdf: int
    fonte: str
    revisado: str
    observacao: str

    @property
    def anos(self) -> set[int]:
        return set(ANOS_POR_CICLO.get(self.ciclo, set()))

    # Aliases para reutilizar o contrato e os renderizadores da Educação Infantil.
    @property
    def objetivo(self) -> str:
        return self.habilidade

    @property
    def campo_experiencia(self) -> str:
        return self.componente

    @property
    def sigla_campo(self) -> str:
        return self.sigla_componente

    @property
    def grupo_etario(self) -> str:
        return self.ano

    @property
    def faixa_etaria(self) -> str:
        return self.ano

    @property
    def grupo_codigo(self) -> str:
        return self.codigo[:4]

    @property
    def texto_busca(self) -> str:
        return normalizar(
            " ".join(
                [
                    self.codigo,
                    self.ano,
                    self.componente,
                    self.habilidade,
                    self.palavras_chave,
                ]
            )
        )

    def como_dicionario(self) -> dict:
        return {
            "codigo": self.codigo,
            "ano": self.ano,
            "ciclo": self.ciclo,
            "componente": self.componente,
            "sigla_componente": self.sigla_componente,
            "habilidade": self.habilidade,
            "pagina_pdf": self.pagina_pdf,
        }


def _resolver_ano(ano: int | str) -> int:
    if isinstance(ano, int):
        numero = ano
    else:
        achado = re.search(r"\d+", str(ano))
        if not achado:
            raise ValueError(f"Ano inválido: {ano!r}")
        numero = int(achado.group())
    if numero < 1 or numero > 5:
        raise ValueError(f"Ano fora do Fundamental I: {ano!r}")
    return numero


def _resolver_componente(componente: str | None) -> str | None:
    if not componente:
        return None
    chave = normalizar(componente)
    if chave.upper() in COMPONENTES:
        return chave.upper()
    for sigla, nome in COMPONENTES.items():
        if normalizar(nome) == chave:
            return sigla
    raise ValueError(f"Componente desconhecido: {componente!r}")


class BaseBNCCEF:
    def __init__(self, csv_path: Path | str = CSV_PADRAO):
        self.csv_path = Path(csv_path)
        self._habilidades = self._carregar_habilidades()
        self._por_codigo = {habilidade.codigo: habilidade for habilidade in self._habilidades}
        if len(self._por_codigo) != len(self._habilidades):
            raise ValueError("A base do Fundamental I contém códigos duplicados.")

    def _carregar_habilidades(self) -> list[HabilidadeEF]:
        with self.csv_path.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo, delimiter=";"))
        habilidades = [
            HabilidadeEF(
                ordem=int(linha["ordem"]),
                codigo=linha["codigo"].strip(),
                etapa=linha["etapa"].strip(),
                ano=linha["ano"].strip(),
                ciclo=linha["ciclo"].strip(),
                componente=linha["componente"].strip(),
                sigla_componente=linha["sigla_componente"].strip(),
                habilidade=linha["habilidade"].strip(),
                palavras_chave=linha["palavras_chave"].strip(),
                pagina_pdf=int(linha["pagina_pdf"]),
                fonte=linha["fonte"].strip(),
                revisado=linha["revisado"].strip(),
                observacao=linha["observacao"].strip(),
            )
            for linha in linhas
        ]
        habilidades.sort(key=lambda habilidade: habilidade.ordem)
        return habilidades

    @property
    def habilidades(self) -> list[HabilidadeEF]:
        return list(self._habilidades)

    def por_codigo(self, codigo: str) -> HabilidadeEF | None:
        return self._por_codigo.get(codigo.strip().upper())

    def anos_disponiveis(self) -> list[int]:
        return [1, 2, 3, 4, 5]

    def componentes_disponiveis(self, ano: int | str) -> list[tuple[str, str]]:
        numero = _resolver_ano(ano)
        siglas = {
            habilidade.sigla_componente
            for habilidade in self._habilidades
            if numero in habilidade.anos
        }
        return [(sigla, COMPONENTES[sigla]) for sigla in COMPONENTES if sigla in siglas]

    def buscar(
        self,
        ano: int | str | None = None,
        componente: str | None = None,
        texto: str | None = None,
    ) -> list[HabilidadeEF]:
        numero = _resolver_ano(ano) if ano is not None else None
        sigla = _resolver_componente(componente)
        tokens = normalizar(texto).split() if texto else []
        padroes = [re.compile(rf"\b{re.escape(token)}") for token in tokens]

        resultados: list[HabilidadeEF] = []
        for habilidade in self._habilidades:
            if numero is not None and numero not in habilidade.anos:
                continue
            if sigla and habilidade.sigla_componente != sigla:
                continue
            if padroes and not all(padrao.search(habilidade.texto_busca) for padrao in padroes):
                continue
            resultados.append(habilidade)
        return resultados

    def selecionar_codigos(
        self,
        ancora: str,
        ano: int | str,
        total: int = 7,
        componentes: int = 4,
        campos: int | None = None,
    ) -> list[HabilidadeEF]:
        """Código âncora + relacionados, sempre dentro da base do Fund. I.

        Regra: mesmo componente primeiro; depois um código por outro
        componente até fechar a quantidade de componentes; por fim, completa
        até o total. Códigos multi-ano entram quando cobrem o ano solicitado.
        """
        ancora_h = self.por_codigo(ancora)
        if ancora_h is None:
            raise CodigoNaoEncontrado(
                f"Não possuo esta informação na minha base de dados: {ancora!r}."
            )

        if campos:
            componentes = campos
        numero = _resolver_ano(ano)
        if numero not in ancora_h.anos:
            raise CodigoNaoEncontrado(
                f"O código {ancora_h.codigo} não pertence ao {numero}º ano."
            )

        candidatos = [
            habilidade
            for habilidade in self._habilidades
            if numero in habilidade.anos and habilidade.codigo != ancora_h.codigo
        ]
        tokens_ancora = set(normalizar(ancora_h.habilidade).split())

        def pontuacao(habilidade: HabilidadeEF) -> tuple[int, str]:
            tokens = set(normalizar(habilidade.habilidade).split())
            return (-len(tokens_ancora & tokens), habilidade.codigo)

        selecionados: list[HabilidadeEF] = [ancora_h]
        usados = {ancora_h.codigo}

        # 1) mesmo componente, até 3 no total (âncora + 2)
        mesmo_componente = sorted(
            [
                habilidade
                for habilidade in candidatos
                if habilidade.sigla_componente == ancora_h.sigla_componente
            ],
            key=pontuacao,
        )
        for habilidade in mesmo_componente:
            if len(selecionados) >= min(3, total):
                break
            if habilidade.codigo not in usados:
                selecionados.append(habilidade)
                usados.add(habilidade.codigo)

        # 2) outros componentes, um por componente, até fechar a quantidade
        por_componente: dict[str, list[HabilidadeEF]] = {}
        for habilidade in candidatos:
            if habilidade.codigo in usados:
                continue
            por_componente.setdefault(habilidade.sigla_componente, []).append(habilidade)

        for sigla in sorted(por_componente):
            if len({h.sigla_componente for h in selecionados}) >= componentes:
                break
            if sigla == ancora_h.sigla_componente:
                continue
            melhor = sorted(por_componente[sigla], key=pontuacao)[0]
            if melhor.codigo not in usados:
                selecionados.append(melhor)
                usados.add(melhor.codigo)

        # 3) completa até o total, preferindo componentes já presentes
        componentes_atuais = {h.sigla_componente for h in selecionados}
        restantes = sorted(
            [
                habilidade
                for habilidade in candidatos
                if habilidade.codigo not in usados
                and habilidade.sigla_componente in componentes_atuais
            ],
            key=pontuacao,
        )
        for habilidade in restantes:
            if len(selecionados) >= total:
                break
            selecionados.append(habilidade)
            usados.add(habilidade.codigo)

        if len(selecionados) < total:
            restantes = sorted(
                [h for h in candidatos if h.codigo not in usados],
                key=pontuacao,
            )
            for habilidade in restantes:
                if len(selecionados) >= total:
                    break
                selecionados.append(habilidade)
                usados.add(habilidade.codigo)

        return selecionados[:total]

    def resumo(self) -> dict:
        por_ciclo: dict[str, int] = {}
        por_componente: dict[str, int] = {}
        for habilidade in self._habilidades:
            por_ciclo[habilidade.ciclo] = por_ciclo.get(habilidade.ciclo, 0) + 1
            por_componente[habilidade.sigla_componente] = (
                por_componente.get(habilidade.sigla_componente, 0) + 1
            )
        return {
            "total": len(self._habilidades),
            "por_ciclo": dict(sorted(por_ciclo.items())),
            "por_componente": dict(sorted(por_componente.items())),
        }

    def codigos(self) -> list[str]:
        return [habilidade.codigo for habilidade in self._habilidades]


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta a BNCC do Fundamental I.")
    parser.add_argument("--ano", help="1 a 5")
    parser.add_argument("--componente", help="LP, AR, EF, ER, MA, CI, GE, HI ou nome")
    parser.add_argument("--texto", default="", help="Busca livre")
    parser.add_argument("--codigo", help="Mostra um código específico")
    parser.add_argument("--selecionar", help="Código âncora para montar 7 habilidades")
    args = parser.parse_args()

    base = BaseBNCCEF()

    if args.selecionar:
        if not args.ano:
            parser.error("--selecionar exige --ano")
        selecionados = base.selecionar_codigos(args.selecionar, args.ano)
        for habilidade in selecionados:
            print(f"{habilidade.codigo}  [{habilidade.componente}]  {habilidade.habilidade[:110]}")
        return 0

    if args.codigo:
        habilidade = base.por_codigo(args.codigo)
        if habilidade is None:
            print(f"Não possuo esta informação na minha base de dados: {args.codigo}")
            return 1
        print(habilidade.como_dicionario())
        return 0

    resultados = base.buscar(ano=args.ano, componente=args.componente, texto=args.texto)
    print(f"Resultados: {len(resultados)}")
    for habilidade in resultados[:30]:
        print(f"{habilidade.codigo}  [{habilidade.ano} • {habilidade.componente}]  {habilidade.habilidade[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
