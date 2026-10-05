from Fotos.services.exif_service import ExifService

from Integrations.ia.factories.gemini_factory import (
    GeminiFactory
)

from Ocorrencias.services.ocorrencia_builder import (
    OcorrenciaBuilder
)


class PreenchimentoAutomaticoFacade:
    """
    Facade responsável por coordenar todo o processo de
    preenchimento automático de uma ocorrência através
    de uma fotografia.
    """

    def __init__(self):
        factory = GeminiFactory()

        self.analisador = factory.criar_analisador()

    def processar(self, arquivo):
        """
        Coordena:
        1. leitura de localização EXIF;
        2. análise visual por IA;
        3. construção dos dados da ocorrência.
        """

        if hasattr(arquivo, "seek"):
            arquivo.seek(0)

        localizacao = ExifService.obter_localizacao(
            arquivo
        )

        if hasattr(arquivo, "seek"):
            arquivo.seek(0)

        analise = self.analisador.analisar(
            arquivo
        )

        builder = OcorrenciaBuilder()

        dados = (
            builder
            .com_localizacao(localizacao)
            .com_analise_ia(analise)
            .construir()
        )

        return dados