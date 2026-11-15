"""Reexporta o pacote de referência para os testes."""

from app.exemplo_pacote import CODIGOS_PLANO, pacote_exemplo


def pacote_gerado_exemplo():
    return pacote_exemplo()


__all__ = ["CODIGOS_PLANO", "pacote_gerado_exemplo"]
