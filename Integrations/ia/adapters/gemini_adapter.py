from Integrations.ia.interfaces import AnalisadorImagem
from Integrations.ia.clients.gemini_client import GeminiClientSingleton


class GeminiAdapter(AnalisadorImagem):
    """
    Adapter responsável por adaptar o Gemini
    para o formato esperado pelo SINU.
    """

    PROMPT = """
    Analise a imagem de uma ocorrência de infraestrutura urbana.

    Retorne:
    - categoria: somente um dos códigos permitidos;
    - descricao: descrição objetiva do problema encontrado.

    Categorias permitidas:

    SB = Saneamento Básico
    PV = Pavimentação e Vias
    IP = Iluminação Pública
    LU = Limpeza Urbana
    AS = Animais em Risco
    AP = Arborização e Praças
    ST = Sinalização de Trânsito
    OS = Obras e Serviços

    Não invente categorias.
    """

    SCHEMA = {
        "type": "object",
        "properties": {
            "categoria": {
                "type": "string",
                "enum": [
                    "SB",
                    "PV",
                    "IP",
                    "LU",
                    "AS",
                    "AP",
                    "ST",
                    "OS"
                ]
            },
            "descricao": {
                "type": "string"
            }
        },
        "required": [
            "categoria",
            "descricao"
        ]
    }

    def __init__(self, cliente=None):
        self.cliente = cliente or GeminiClientSingleton()

    def analisar(self, arquivo):
        return self.cliente.gerar_conteudo(
            arquivo=arquivo,
            prompt=self.PROMPT,
            schema=self.SCHEMA
        )