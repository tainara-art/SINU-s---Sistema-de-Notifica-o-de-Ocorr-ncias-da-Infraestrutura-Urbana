class OcorrenciaBuilder:
    """
    Builder responsável por montar gradualmente os dados
    utilizados no preenchimento de uma ocorrência.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._dados = {
            "categoria": None,
            "descricao": None,
            "latitude": None,
            "longitude": None,
        }

        return self

    def com_analise_ia(self, analise):
        if analise:
            self._dados["categoria"] = analise.get(
                "categoria"
            )

            self._dados["descricao"] = analise.get(
                "descricao"
            )

        return self

    def com_localizacao(self, localizacao):
        if localizacao:
            self._dados["latitude"] = localizacao.get(
                "latitude"
            )

            self._dados["longitude"] = localizacao.get(
                "longitude"
            )

        return self

    def construir(self):
        resultado = self._dados.copy()

        self.reset()

        return resultado