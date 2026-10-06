from abc import ABC, abstractmethod


class AnalisadorFactory(ABC):
    """
    Contrato para fábricas responsáveis por criar
    analisadores de imagem.
    """

    @abstractmethod
    def criar_analisador(self):
        pass