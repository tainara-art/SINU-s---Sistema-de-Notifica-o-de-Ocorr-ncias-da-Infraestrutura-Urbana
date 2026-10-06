from Integrations.ia.factories.abstract_factory import (
    AnalisadorFactory
)

from Integrations.ia.clients.gemini_client import (
    GeminiClientSingleton
)

from Integrations.ia.adapters.gemini_adapter import (
    GeminiAdapter
)

from Integrations.ia.decorators.validacao_decorator import (
    ValidacaoDecorator
)


class GeminiFactory(AnalisadorFactory):
    """
    Factory responsável por montar o analisador Gemini
    utilizado pelo SINU.
    """

    def criar_analisador(self):
        cliente = GeminiClientSingleton()

        adapter = GeminiAdapter(
            cliente=cliente
        )

        analisador = ValidacaoDecorator(
            adapter
        )

        return analisador