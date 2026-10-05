from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from rest_framework.response import Response

from Fotos.services.exif_service import ExifService
from Ocorrencias.forms import FotoUploadForm


@require_http_methods(['GET', 'POST'])
def upload_foto(request):
    form = FotoUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        # View utilitaria mantida para compatibilidade com o prototipo.
        # O fluxo principal de fotos ocorre pelo OcorrenciaSerializer.
        messages.success(request, 'Foto recebida com sucesso!')
        return redirect(request.path)

    return render(request, 'ocorrencias/upload.html', {'form': form})
 
class LocalizacaoFotoView(APIView):
    """
    Recebe uma imagem enviada pelo frontend e tenta extrair
    sua localização GPS através dos metadados EXIF.

    A leitura e conversão dos metadados ficam sob responsabilidade
    do ExifService; a view apenas trata HTTP e devolve o resultado.
    """
    def post(self, request):
        arquivo = request.FILES.get("foto")
        
        if not arquivo:
            return Response(
                {"erro": "Imagem não enviada"},
                status=400
            )
        localizacao = ExifService.obter_localizacao(arquivo)

        if not localizacao:
            return Response (
                {"erro": "Imagem sem localização GPS"},
                status=400
            )
        return Response(localizacao)
