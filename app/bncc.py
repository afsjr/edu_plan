"""Consulta local à base da BNCC de Educação Infantil.

Para 93 registros não é necessário banco nem embedding: a base é carregada em
memória e filtrada de forma determinística. Quando a base crescer para o
Fundamental I, a mesma interface pode ser mantida e trocada por Postgres/pgvector.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV_PADRAO = RAIZ / "data" / "bncc" / "bncc_ei.csv"
MAPA_PADRAO = RAIZ / "data" / "bncc" / "mapeamento_escolar.csv"

CAMPOS = {
    "EO": "O eu, o outro e o nós",
    "CG": "Corpo, gestos e movimentos",
    "TS": "Traços, sons, cores e formas",
    "EF": "Escuta, fala, pensamento e imaginação",
    "ET": "Espaços, tempos, quantidades, relações e transformações",
}

GRUPOS = {
    "EI01": "Bebês",
    "EI02": "Crianças bem pequenas",
    "EI03": "Crianças pequenas",
}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação, para busca tolerante."""
    sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sem_acento).strip()


class CodigoNaoEncontrado(ValueError):
    """O código não existe na base ou não pertence à turma solicitada."""


@dataclass(frozen=True)
class Habilidade:
    ordem: int
    codigo: str
    etapa: str
    grupo_etario: str
    faixa_etaria: str
    campo_experiencia: str
    sigla_campo: str
    objetivo: str
    palavras_chave: str
    pagina_pdf: int
    fonte: str
    revisado: str
    observacao: str

    @property
    def grupo_codigo(self) -> str:
        return self.codigo[:4]

    @property
    def texto_busca(self) -> str:
        return normalizar(
            " ".join(
                [
                    self.codigo,
                    self.grupo_etario,
                    self.campo_experiencia,
                    self.objetivo,
                    self.palavras_chave,
                ]
            )
        )

    def como_dicionario(self) -> dict:
        return {
            "codigo": self.codigo,
            "grupo_codigo": self.grupo_codigo,
            "grupo_etario": self.grupo_etario,
            "faixa_etaria": self.faixa_etaria,
            "campo_experiencia": self.campo_experiencia,
            "sigla_campo": self.sigla_campo,
            "objetivo": self.objetivo,
            "pagina_pdf": self.pagina_pdf,
        }


class BaseBNCC:
    def __init__(self, csv_path: Path | str = CSV_PADRAO, mapa_path: Path | str = MAPA_PADRAO):
        self.csv_path = Path(csv_path)
        self.mapa_path = Path(mapa_path)
        self._habilidades = self._carregar_habilidades()
        self._por_codigo = {habilidade.codigo: habilidade for habilidade in self._habilidades}
        self._uso_para_grupo = self._carregar_mapeamento()

        if len(self._por_codigo) != len(self._habilidades):
            raise ValueError("A base contém códigos duplicados.")

    def _carregar_habilidades(self) -> list[Habilidade]:
        with self.csv_path.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo, delimiter=";"))

        habilidades = [
            Habilidade(
                ordem=int(linha["ordem"]),
                codigo=linha["codigo"].strip(),
                etapa=linha["etapa"].strip(),
                grupo_etario=linha["grupo_etario"].strip(),
                faixa_etaria=linha["faixa_etaria"].strip(),
                campo_experiencia=linha["campo_experiencia"].strip(),
                sigla_campo=linha["sigla_campo"].strip(),
                objetivo=linha["objetivo"].strip(),
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

    def _carregar_mapeamento(self) -> dict[str, list[str]]:
        self._uso_rotulos: dict[str, str] = {}
        if not self.mapa_path.exists():
            return {}
        with self.mapa_path.open(encoding="utf-8-sig", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo, delimiter=";"))

        mapa: dict[str, list[str]] = {}
        for linha in linhas:
            rotulo = linha["uso_escolar_sugerido"].strip()
            uso = normalizar(rotulo)
            self._uso_rotulos[uso] = rotulo
            grupo = linha["codigo_grupo"].strip()
            mapa.setdefault(uso, [])
            if grupo not in mapa[uso]:
                mapa[uso].append(grupo)
        return mapa

    @property
    def habilidades(self) -> list[Habilidade]:
        return list(self._habilidades)

    def por_codigo(self, codigo: str) -> Habilidade | None:
        return self._por_codigo.get(codigo.strip().upper())

    def usos_escolares(self) -> list[str]:
        return sorted(self._uso_rotulos.values(), key=normalizar)

    def _resolver_grupo(self, grupo: str | None) -> str | None:
        if not grupo:
            return None
        chave = normalizar(grupo)
        if chave.upper().startswith("EI") and chave.upper() in GRUPOS:
            return chave.upper()
        for codigo, nome in GRUPOS.items():
            if normalizar(nome) == chave:
                return codigo
        grupos = self._uso_para_grupo.get(chave)
        if grupos and len(grupos) == 1:
            return grupos[0]
        if grupos:
            raise ValueError(
                f"O uso escolar {grupo!r} corresponde a mais de um grupo ({', '.join(grupos)}). "
                "Filtre também pelo código do grupo."
            )
        raise ValueError(f"Grupo ou uso escolar desconhecido: {grupo!r}")

    def _resolver_campo(self, campo: str | None) -> str | None:
        if not campo:
            return None
        chave = normalizar(campo)
        if chave.upper() in CAMPOS:
            return chave.upper()
        for sigla, nome in CAMPOS.items():
            if normalizar(nome) == chave:
                return sigla
        raise ValueError(f"Campo de experiência desconhecido: {campo!r}")

    def buscar(
        self,
        grupo: str | None = None,
        campo: str | None = None,
        texto: str | None = None,
        uso_escolar: str | None = None,
    ) -> list[Habilidade]:
        grupo_codigo = self._resolver_grupo(grupo or uso_escolar)
        sigla = self._resolver_campo(campo)
        tokens = normalizar(texto).split() if texto else []
        padroes = [re.compile(rf"\b{re.escape(token)}") for token in tokens]

        resultados: list[Habilidade] = []
        for habilidade in self._habilidades:
            if grupo_codigo and habilidade.grupo_codigo != grupo_codigo:
                continue
            if sigla and habilidade.sigla_campo != sigla:
                continue
            if padroes and not all(padrao.search(habilidade.texto_busca) for padrao in padroes):
                continue
            resultados.append(habilidade)
        return resultados

    def candidatos_para(
        self,
        uso_escolar: str,
        campo: str | None = None,
        texto: str | None = None,
    ) -> list[Habilidade]:
        return self.buscar(uso_escolar=uso_escolar, campo=campo, texto=texto)

    def selecionar_codigos(
        self,
        ancora: str,
        uso_escolar: str,
        total: int = 7,
        campos: int = 4,
    ) -> list[Habilidade]:
        """Código âncora + relacionados, sempre dentro de data/bncc.

        Regra: mesmo campo primeiro; depois um código por outro campo até
        fechar a quantidade de campos; por fim, completa até o total.
        """
        ancora_h = self.por_codigo(ancora)
        if ancora_h is None:
            raise CodigoNaoEncontrado(
                f"Não possuo esta informação na minha base de dados: {ancora!r}."
            )

        grupo = self._resolver_grupo(uso_escolar)
        if ancora_h.grupo_codigo != grupo:
            raise CodigoNaoEncontrado(
                f"O código {ancora_h.codigo} não pertence à turma {uso_escolar}."
            )

        candidatos = [
            habilidade
            for habilidade in self._habilidades
            if habilidade.grupo_codigo == grupo and habilidade.codigo != ancora_h.codigo
        ]
        tokens_ancora = set(normalizar(ancora_h.objetivo).split())

        def pontuacao(habilidade: Habilidade) -> tuple[int, str]:
            tokens = set(normalizar(habilidade.objetivo).split())
            return (-len(tokens_ancora & tokens), habilidade.codigo)

        selecionados: list[Habilidade] = [ancora_h]
        usados = {ancora_h.codigo}

        # 1) mesmo campo, até 3 no total (âncora + 2)
        mesmo_campo = sorted(
            [h for h in candidatos if h.sigla_campo == ancora_h.sigla_campo],
            key=pontuacao,
        )
        for habilidade in mesmo_campo:
            if len(selecionados) >= min(3, total):
                break
            if habilidade.codigo not in usados:
                selecionados.append(habilidade)
                usados.add(habilidade.codigo)

        # 2) outros campos, um por campo, até fechar a quantidade de campos
        por_campo: dict[str, list[Habilidade]] = {}
        for habilidade in candidatos:
            if habilidade.codigo in usados:
                continue
            por_campo.setdefault(habilidade.sigla_campo, []).append(habilidade)

        for sigla in sorted(por_campo):
            if len({h.sigla_campo for h in selecionados}) >= campos:
                break
            if sigla == ancora_h.sigla_campo:
                continue
            melhor = sorted(por_campo[sigla], key=pontuacao)[0]
            if melhor.codigo not in usados:
                selecionados.append(melhor)
                usados.add(melhor.codigo)

        # 3) completa até o total, preferindo campos já presentes
        campos_atuais = {h.sigla_campo for h in selecionados}
        restantes = sorted(
            [
                h
                for h in candidatos
                if h.codigo not in usados and h.sigla_campo in campos_atuais
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

    def codigos(self) -> list[str]:
        return [habilidade.codigo for habilidade in self._habilidades]

    def resumo(self) -> dict:
        por_grupo: dict[str, int] = {}
        por_campo: dict[str, int] = {}
        for habilidade in self._habilidades:
            por_grupo[habilidade.grupo_codigo] = por_grupo.get(habilidade.grupo_codigo, 0) + 1
            por_campo[habilidade.sigla_campo] = por_campo.get(habilidade.sigla_campo, 0) + 1
        return {
            "total": len(self._habilidades),
            "por_grupo": dict(sorted(por_grupo.items())),
            "por_campo": dict(sorted(por_campo.items())),
            "usos_escolares": self.usos_escolares(),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Consulta a base da BNCC de Educação Infantil.")
    parser.add_argument("--grupo", help="EI01, EI02, EI03 ou nome do grupo etário")
    parser.add_argument("--uso", help="Berçário, Maternal, Pré I ou Pré II")
    parser.add_argument("--campo", help="EO, CG, TS, EF, ET ou nome do campo")
    parser.add_argument("--texto", help="Trecho do objetivo ou palavra-chave")
    parser.add_argument("--limite", type=int, default=20, help="Máximo de resultados")
    args = parser.parse_args()

    base = BaseBNCC()
    resultados = base.buscar(
        grupo=args.grupo,
        campo=args.campo,
        texto=args.texto,
        uso_escolar=args.uso,
    )

    print(base.resumo())
    print()
    for habilidade in resultados[: args.limite]:
        print(f"{habilidade.codigo} | {habilidade.grupo_etario} | {habilidade.campo_experiencia}")
        print(f"  {habilidade.objetivo}")
    if len(resultados) > args.limite:
        print(f"... {len(resultados) - args.limite} resultado(s) omitido(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
