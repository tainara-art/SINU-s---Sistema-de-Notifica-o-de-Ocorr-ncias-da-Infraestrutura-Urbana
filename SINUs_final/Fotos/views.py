from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

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
