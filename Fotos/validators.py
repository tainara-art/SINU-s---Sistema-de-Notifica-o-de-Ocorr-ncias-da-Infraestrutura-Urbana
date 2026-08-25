import os

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

# Apenas imagens/fotos. PDFs, documentos, executáveis e outros anexos não são aceitos.
EXTENSOES_IMAGEM_PERMITIDAS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.jfif']
TIPOS_MIME_IMAGEM_PERMITIDOS = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
}
MAX_FOTOS_POR_OCORRENCIA = 5


def validate_image_file(arquivo):
    """Valida se o upload é realmente uma imagem permitida."""
    if not arquivo:
        return arquivo

    nome = getattr(arquivo, 'name', '') or ''
    extensao = os.path.splitext(nome)[1].lower()
    if extensao not in EXTENSOES_IMAGEM_PERMITIDAS:
        raise ValidationError(
            'Tipo de arquivo não permitido. Envie somente fotos nos formatos: JPG, JPEG, PNG, WEBP, GIF ou JFIF.'
        )

    content_type = getattr(arquivo, 'content_type', None)
    if content_type and content_type.lower() not in TIPOS_MIME_IMAGEM_PERMITIDOS:
        raise ValidationError(
            'Tipo de arquivo inválido. O campo de foto aceita somente arquivos de imagem.'
        )

    try:
        posicao_atual = arquivo.tell() if hasattr(arquivo, 'tell') else None
    except Exception:
        posicao_atual = None

    try:
        imagem = Image.open(arquivo)
        imagem.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(
            'Arquivo inválido. Envie uma foto válida nos formatos JPG, JPEG, PNG, WEBP, GIF ou JFIF.'
        )
    finally:
        if hasattr(arquivo, 'seek'):
            arquivo.seek(posicao_atual or 0)

    return arquivo
