from app.icons import BancoIcones, icone_para, normalizar


def test_normalizacao():
    assert normalizar("ABACAXI") == "abacaxi"
    assert normalizar("João-de-barro") == "joao de barro"
    assert normalizar("  cor   laranja ") == "cor laranja"


def test_icones_conhecidos():
    assert icone_para("ABACAXI") == "🍍"
    assert icone_para("BOLA") == "⚽"
    assert icone_para("CACHORRO") == "🐶"
    assert icone_para("DADO") == "🎲"


def test_plural_e_sinonimo():
    assert icone_para("ABACAXIS") == "🍍"
    assert icone_para("COR LARANJA") == "🟠"


def test_fallback():
    assert icone_para("PALAVRA QUE NAO EXISTE") == "✨"


def test_base_carrega():
    banco = BancoIcones()
    assert len(banco.chaves()) >= 40
    assert "abacaxi" in banco.chaves()
