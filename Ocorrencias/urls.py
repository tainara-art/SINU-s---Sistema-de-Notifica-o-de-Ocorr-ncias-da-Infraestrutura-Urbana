from django.urls import path

from .views import PreenchimentoAutomaticoView


urlpatterns = [
    path(
        "preenchimento-automatico/",
        PreenchimentoAutomaticoView.as_view(),
        name="preenchimento-automatico",
    ),
]