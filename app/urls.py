"""
URL Configuration — PI_SINUS_MERGED

Organização:
  /            → Frontend (Django Templates)
  /api/...     → Backend (API REST + JWT)
  /admin/      → Django Admin
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from Prefeitura.views  import PrefeituraListCreate, PrefeituraRetrieveUpdateDestroy
from Secretaria.views  import SecretariaListCreate, SecretariaRetrieveUpdateDestroy
from Ocorrencias.views import (
    OcorrenciaCreateList,
    OcorrenciaRetrieveUpdateDestroy,
    OcorrenciasGeoJSONView,
    RegistrarOcorrenciaMapaView,
)
from Usuario.views import UsuarioCreate, UsuarioRetrieveUpdate, UsuarioLogin

# ── Frontend (Templates Django) ────────────────────────────────────────────
frontend_urls = [
    path('', include('frontend.urls')),
]

# ── API REST ───────────────────────────────────────────────────────────────
api_urls = [
    # Prefeitura
    path('prefeitura/',           PrefeituraListCreate.as_view(),            name='api-prefeitura-list'),
    path('prefeitura/<int:pk>/',  PrefeituraRetrieveUpdateDestroy.as_view(), name='api-prefeitura-detail'),

    # Secretaria
    path('secretaria/',           SecretariaListCreate.as_view(),            name='api-secretaria-list'),
    path('secretaria/<int:pk>/',  SecretariaRetrieveUpdateDestroy.as_view(), name='api-secretaria-detail'),

    # Ocorrências
    path('ocorrencia/',              OcorrenciaCreateList.as_view(),             name='api-ocorrencia-list'),
    path('ocorrencia/<int:pk>/',     OcorrenciaRetrieveUpdateDestroy.as_view(),  name='api-ocorrencia-detail'),
    path('ocorrencia/mapa/',         OcorrenciasGeoJSONView.as_view(),           name='api-ocorrencias-geojson'),
    path('ocorrencia/registrar/',    RegistrarOcorrenciaMapaView.as_view(),      name='api-ocorrencia-registrar'),

    # Usuário
    path('cadastro/',  UsuarioCreate.as_view(),        name='api-usuario-create'),
    path('perfil/',    UsuarioRetrieveUpdate.as_view(), name='api-usuario-perfil'),
    path('login/',     UsuarioLogin.as_view(),          name='api-usuario-login'),

    # JWT
    path('authentication/token/',         TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('authentication/token/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),
    path('authentication/token/verify/',  TokenVerifyView.as_view(),      name='token_verify'),

    # DRF browsable API (apenas em DEBUG)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    #asfotolá
    path("fotos/", include("Fotos.urls")),
]

urlpatterns = (
    frontend_urls
    + [
        path('admin/', admin.site.urls),
        path('api/',   include(api_urls)),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)
