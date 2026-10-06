from core.choices import CategoriaOcorrencia

from Integrations.ia.decorators.analisador_decorator import (
    AnalisadorDecorator
)


class ValidacaoDecorator(AnalisadorDecorator):
    """
    Valida a resposta produzida pelo analisador de imagem
    antes de entregá-la ao restante do sistema.
    """

    def analisar(self, arquivo):
        resultado = super().analisar(arquivo)

        if not isinstance(resultado, dict):
            raise ValueError("Resposta da IA em formato inválido.")

        categoria = resultado.get("categoria")
        descricao = resultado.get("descricao")

        categorias_validas = {
            codigo
            for codigo, _ in CategoriaOcorrencia.choices
        }

        if categoria not in categorias_validas:
            raise ValueError(
                f"Categoria inválida retornada pela IA: {categoria}"
            )

        if not descricao or not descricao.strip():
            raise ValueError(
                "A IA não retornou uma descrição válida."
            )

        return {
            "categoria": categoria,
            "descricao": descricao.strip()
        }