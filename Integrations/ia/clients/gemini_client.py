from django.conf import settings
from google import genai
from google.genai import types

from Integrations.ia.interfaces import ClienteIA


class GeminiClientSingleton(ClienteIA):
    """
    Singleton responsável por manter uma única instância
    do cliente Gemini por processo Python.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")

        self.client = genai.Client(api_key=api_key)
        self.model = settings.GEMINI_MODEL

        self._initialized = True

    def gerar_conteudo(self, arquivo, prompt, schema):
        """
        Envia a imagem ao Gemini e solicita uma resposta
        estruturada conforme o schema informado.
        """

        if hasattr(arquivo, "seek"):
            arquivo.seek(0)

        imagem_bytes = arquivo.read()

        mime_type = getattr(
            arquivo,
            "content_type",
            "image/jpeg"
        )

        imagem = types.Part.from_bytes(
            data=imagem_bytes,
            mime_type=mime_type
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                prompt,
                imagem
            ],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": schema
            }
        )

        if hasattr(arquivo, "seek"):
            arquivo.seek(0)

        return response.parsed