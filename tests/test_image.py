from app import image
from app.bncc import BaseBNCC
from app.contract import resolver_pacote
from app.exemplo_pacote import pacote_exemplo
from app.pipeline import enriquecer_imagens


def _caderno_e_plano():
    base = BaseBNCC()
    permitidos = {h.codigo for h in base.buscar(grupo="EI03")}
    pacote = resolver_pacote(pacote_exemplo(), base, permitidos)
    return pacote.caderno, pacote.plano


def test_prompt_seguro():
    prompt = image.montar_prompt("uma maçã", "Meu nome")
    assert "uma maçã" in prompt
    assert "no text" in prompt
    assert "no letters" in prompt


def test_disponivel_false_no_mock(monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "mock")
    assert not image.disponivel()


def test_enriquecer_imagens(monkeypatch):
    caderno, plano = _caderno_e_plano()
    monkeypatch.setenv("IMAGE_PROVIDER", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "conta")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setattr(image, "gerar_imagem", lambda prompt: "a" * 2000)

    novo = enriquecer_imagens(caderno, plano)
    com_imagem = [a for a in novo.atividades if a.imagem_base64]
    assert len(com_imagem) == 5
    assert novo.imagem_status


def test_gera_para_todas_as_atividades(monkeypatch):
    caderno, plano = _caderno_e_plano()
    monkeypatch.setenv("IMAGE_PROVIDER", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "conta")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    monkeypatch.setattr(image, "gerar_imagem", lambda prompt: "a" * 2000)

    novo = enriquecer_imagens(caderno, plano)
    assert all(a.imagem_base64 for a in novo.atividades)
