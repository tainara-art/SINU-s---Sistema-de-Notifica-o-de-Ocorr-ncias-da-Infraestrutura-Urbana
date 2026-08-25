# frontend/urls.py
from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Páginas públicas
    path('',                        views.landing_page,            name='landing'),
    path('entrar/',                 views.login_view,              name='login'),
    path('sair/',                   views.logout_view,             name='logout'),
    path('cadastro/',               views.cadastro_usuario_view,   name='cadastro_usuario'),
    path('ocorrencia-anonima/',     views.ocorrencia_anonima_view, name='ocorrencia_anonima'),

    # Dashboard (roteado por perfil)
    path('painel/',                 views.dashboard_view,          name='dashboard'),

    # Alterar senha obrigatória (prefeitura/secretaria)
    path('alterar-senha/',          views.alterar_senha_view,      name='alterar_senha'),

    # CRUD Prefeituras
    path('painel/prefeituras/',                          views.prefeituras_view,         name='prefeituras'),
    path('painel/prefeituras/<int:pk>/editar/',          views.prefeitura_editar_view,   name='prefeitura_editar'),
    path('painel/prefeituras/<int:pk>/excluir/',         views.prefeitura_excluir_view,  name='prefeitura_excluir'),

    # CRUD Secretarias
    path('painel/secretarias/',                          views.secretarias_view,         name='secretarias'),
    path('painel/secretarias/<int:pk>/editar/',          views.secretaria_editar_view,   name='secretaria_editar'),
    path('painel/secretarias/<int:pk>/excluir/',         views.secretaria_excluir_view,  name='secretaria_excluir'),
]
