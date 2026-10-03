from django.urls import path
from .views import LocalizacaoFotoView

urlpatterns = [
    path(
        "localizacao/", LocalizacaoFotoView.as_view(), name="foto-localizacao"
    ),
]