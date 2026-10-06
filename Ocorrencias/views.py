# Ocorrencias/views.py
from datetime import timedelta

from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Ocorrencia, HistoricoStatus
from .serializers import OcorrenciaSerializer
from Secretaria.models import Secretaria

from rest_framework.views import APIView
from rest_framework.response import Response
from google.genai import errors as genai_errors

from Ocorrencias.services.preenchimento_automatico_facade import (
    PreenchimentoAutomaticoFacade
)
CORES_CATEGORIA = {
    'SB': '#1E90FF', 'PV': '#FF8C00', 'IP': '#FFD700', 'LU': '#32CD32',
    'AS': '#FF69B4', 'AP': '#228B22', 'ST': '#DC143C', 'OS': '#8B4513',
}
ICONES_CATEGORIA = {
    'SB': '💧', 'PV': '🚧', 'IP': '💡', 'LU': '🗑️',
    'AS': '🐾', 'AP': '🌳', 'ST': '🚦', 'OS': '🏗️',
}


def buscar_ocorrencia_duplicada(dados, janela_segundos=10):
    """
    Evita duplicidade causada por duplo clique, reenvio do formulário
    ou duas chamadas de API muito próximas com o mesmo conteúdo.

    A validação é curta de propósito: o cidadão ainda pode registrar
    a mesma ocorrência novamente em outro momento, se fizer sentido.
    """
    descricao = (dados.get('descricao') or '').strip()
    categoria = dados.get('categoria')
    prefeitura = dados.get('prefeitura')
    latitude = dados.get('latitude')
    longitude = dados.get('longitude')

    if not all([descricao, categoria, prefeitura, latitude, longitude]):
        return None

    anonima_raw = dados.get('anonima')
    if isinstance(anonima_raw, str):
        anonima = anonima_raw.strip().lower() in {'1', 'true', 'sim', 'yes', 'on'}
    else:
        anonima = bool(anonima_raw)

    limite = timezone.now() - timedelta(seconds=janela_segundos)
    qs = Ocorrencia.objects.filter(
        descricao=descricao,
        categoria=categoria,
        prefeitura=prefeitura,
        latitude=latitude,
        longitude=longitude,
        cep=dados.get('cep') or '',
        anonima=anonima,
        date_created__gte=limite,
    )

    usuario = dados.get('usuario')
    if anonima or usuario is None:
        qs = qs.filter(usuario__isnull=True)
    else:
        qs = qs.filter(usuario=usuario)

    return qs.order_by('-date_created').first()


class OcorrenciaCreateList(generics.ListCreateAPIView):
    queryset = Ocorrencia.objects.all().select_related(
        'prefeitura', 'secretaria', 'usuario'
    ).prefetch_related('fotos_da_ocorrencia')
    serializer_class   = OcorrenciaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dados = dict(serializer.validated_data)
        if not dados.get('anonima') and request.user.is_authenticated and not dados.get('usuario'):
            dados['usuario'] = request.user

        duplicada = buscar_ocorrencia_duplicada(dados)
        if duplicada:
            return Response(
                {
                    'ok': True,
                    'duplicada': True,
                    'id': duplicada.id,
                    'mensagem': 'Ocorrência já registrada. A duplicidade foi evitada.',
                },
                status=status.HTTP_200_OK,
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        if (
            not serializer.validated_data.get('anonima')
            and self.request.user.is_authenticated
            and not serializer.validated_data.get('usuario')
        ):
            serializer.save(usuario=self.request.user)
        else:
            serializer.save()


class OcorrenciaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Ocorrencia.objects.all()
    serializer_class   = OcorrenciaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OcorrenciasGeoJSONView(APIView):
    """GeoJSON para o mapa Leaflet — suporta filtros via query params."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        qs = Ocorrencia.objects.select_related('prefeitura', 'secretaria')

        categoria  = request.GET.get('categoria')
        status_val = request.GET.get('status')
        prefeitura = request.GET.get('prefeitura')
        secretaria = request.GET.get('secretaria')

        if categoria:  qs = qs.filter(categoria=categoria)
        if status_val: qs = qs.filter(status=status_val)
        if prefeitura: qs = qs.filter(prefeitura_id=prefeitura)
        if secretaria: qs = qs.filter(secretaria_id=secretaria)

        features = []
        for oc in qs:
            if oc.latitude is None or oc.longitude is None:
                continue
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(oc.longitude), float(oc.latitude)],
                },
                'properties': {
                    'id':            oc.id,
                    'descricao':     oc.descricao,
                    'categoria':     oc.get_categoria_display(),
                    'categoria_cod': oc.categoria,
                    'status':        oc.get_status_display(),
                    'status_cod':    oc.status,
                    'prioridade':    oc.get_prioridade_display(),
                    'anonima':       oc.anonima,
                    'prefeitura':    oc.prefeitura.name if oc.prefeitura else None,
                    'secretaria':    oc.secretaria.name if oc.secretaria else None,
                    'criado_em':     oc.date_created.strftime('%d/%m/%Y %H:%M'),
                    'cor':           CORES_CATEGORIA.get(oc.categoria, '#888888'),
                    'icone':         ICONES_CATEGORIA.get(oc.categoria, '📍'),
                },
            })

        return JsonResponse({
            'type':     'FeatureCollection',
            'total':    len(features),
            'features': features,
        })


class RegistrarOcorrenciaMapaView(APIView):
    """Recebe clique no mapa, salva a ocorrência e cria o histórico inicial."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            lat = float(request.data.get('latitude'))
            lng = float(request.data.get('longitude'))
        except (TypeError, ValueError):
            return Response(
                {'erro': 'Coordenadas inválidas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (-33.8 <= lat <= 5.3 and -73.9 <= lng <= -28.8):
            return Response(
                {'erro': 'Coordenadas fora do território brasileiro.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        categoria     = request.data.get('categoria')
        prefeitura_id = request.data.get('prefeitura')

        # RF03.2 / RN02 — encaminhamento automático para secretaria
        secretaria_id = None
        try:
            sec = Secretaria.objects.get(
                prefeitura_id=prefeitura_id,
                categoria=categoria
            )
            secretaria_id = sec.id
        except Secretaria.DoesNotExist:
            pass

        # RN01 — ocorrência anônima não vincula usuário
        usuario_id = None
        if not request.data.get('anonima'):
            usuario_id = request.user.id

        dados_ocorrencia = {
            **request.data,
            'latitude':   lat,
            'longitude':  lng,
            'usuario':    request.user if usuario_id else None,
            'secretaria': secretaria_id,
            'status':     'AB',
        }

        duplicada = buscar_ocorrencia_duplicada(dados_ocorrencia)
        if duplicada:
            return Response(
                {
                    'ok': True,
                    'duplicada': True,
                    'id': duplicada.id,
                    'mensagem': 'Ocorrência já registrada. A duplicidade foi evitada.',
                },
                status=status.HTTP_200_OK,
            )

        serializer = OcorrenciaSerializer(data={
            **request.data,
            'latitude':   lat,
            'longitude':  lng,
            'usuario':    usuario_id,
            'secretaria': secretaria_id,
            'status':     'AB',
        })

        if serializer.is_valid():
            oc = serializer.save()
            # RF21 / RN05 — primeiro registro no histórico
            HistoricoStatus.objects.create(
                ocorrencia=oc,
                status_anterior='',
                status_novo='AB',
                observacao='Ocorrência registrada.',
                responsavel=request.user,
            )
            return Response(
                {'ok': True, 'id': oc.id},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {'ok': False, 'erros': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
class PreenchimentoAutomaticoView(APIView):
    """
    Analisa uma foto antes do cadastro da ocorrência.
    """

    def post(self, request):
        arquivo = request.FILES.get("foto")

        if not arquivo:
            return Response(
                {"erro": "Imagem não enviada"},
                status=400
            )

        try:
            facade = PreenchimentoAutomaticoFacade()
            dados = facade.processar(arquivo)

            return Response(dados)

        except ValueError as erro:
            return Response(
                {"erro": str(erro)},
                status=422
            )

        except genai_errors.APIError:
            return Response(
                {
                    "erro": (
                        "O serviço de inteligência artificial "
                        "está temporariamente indisponível."
                    )
                },
                status=503
            )
