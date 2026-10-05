from Integrations.ia.interfaces import AnalisadorImagem


class AnalisadorDecorator(AnalisadorImagem):
    """
    Decorator base para analisadores de imagem.
    """

    def __init__(self, analisador):
        self._analisador = analisador

    def analisar(self, arquivo):
        return self._analisador.analisar(arquivo)