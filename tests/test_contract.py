import pytest

from app.bncc import BaseBNCC
from app.contract import (
    CodigoBNCCInvalido,
    ErroContrato,
    exportar_schema,
    resolver_pacote,
)
from app.exemplo_pacote import pacote_exemplo


@pytest.fixture(scope="module")
def base():
    return BaseBNCC()


@pytest.fixture
def permitidos(base):
    return {habilidade.codigo for habilidade in base.buscar(uso_escolar="Pré II")}


def test_resolve_exemplo(base, permitidos):
    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    assert len(pacote.plano.habilidades) == 7
    assert len(pacote.caderno.atividades) == 5
    assert pacote.avisos == []
    assert pacote.plano.habilidades[0].descricao.startswith("Demonstrar empatia")
    assert pacote.caderno.atividades[0].campo_experiencia


def test_rejeita_codigo_fora_da_lista(base, permitidos):
    with pytest.raises(CodigoBNCCInvalido):
        resolver_pacote(pacote_exemplo(), base, {"EI03EF01"})


def test_rejeita_codigo_inexistente(base):
    gerado = pacote_exemplo()
    gerado.plano.habilidades[0].codigo = "EI03XX99"
    with pytest.raises(CodigoBNCCInvalido):
        resolver_pacote(gerado, base, None)


def test_exige_cinco_atividades(base, permitidos):
    gerado = pacote_exemplo()
    gerado.caderno.atividades = gerado.caderno.atividades[:4]
    with pytest.raises(ErroContrato):
        resolver_pacote(gerado, base, permitidos)


def test_exportar_schema(tmp_path):
    destino = exportar_schema(tmp_path / "schema.json")
    assert destino.exists()
    conteudo = destino.read_text(encoding="utf-8")
    assert "PacoteGerado" in conteudo
    assert "codigo_bncc" in conteudo
