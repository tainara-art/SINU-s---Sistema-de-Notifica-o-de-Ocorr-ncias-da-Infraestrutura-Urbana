from abc import ABC, abstractmethod


class ClienteIA(ABC):
    """
    Contrato para clientes de provedores de Inteligência Artificial.
    """

    @abstractmethod
    def gerar_conteudo(self, arquivo, prompt, schema):
        """
        Envia um arquivo para o provedor de IA e retorna
        uma resposta estruturada.
        """
        pass


class AnalisadorImagem(ABC):
    """
    Contrato utilizado pelo SINU para análise de imagens.
    """

    @abstractmethod
    def analisar(self, arquivo):
        """
        Analisa uma imagem e retorna os dados sugeridos
        para preenchimento da ocorrência.
        """
        pass