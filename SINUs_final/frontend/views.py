# frontend/views.py
#
# Views Django (sessão/templates) do SINUS.
# Adaptado para usar CategoriaOcorrencia (choices) em vez do model Categoria.

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.choices       import CategoriaOcorrencia
from Ocorrencias.models import Ocorrencia, StatusOcorrencia
from Prefeitura.models  import Prefeitura
from Secretaria.models  import Secretaria

from .forms import (
    AlterarSenhaForm,
    LoginForm,
    OcorrenciaForm,
    PrefeituraForm,
    SecretariaForm,
    UsuarioCadastroForm,
)


# ---------------------------------------------------------------------------
# Helper: detectar perfil do usuário logado
# ---------------------------------------------------------------------------

def _perfil(user):
    """Retorna 'admin', 'prefeitura', 'secretaria' ou 'usuario'."""
    if user.is_staff or user.is_superuser:
        return 'admin'
    if hasattr(user, 'prefeitura'):
        return 'prefeitura'
    if hasattr(user, 'secretaria_vinculada'):
        return 'secretaria'
    return 'usuario'




def _ocorrencias_mapa_payload(ocorrencias):
    """Monta dados seguros para exibição das ocorrências nos mapas dos painéis."""
    pontos = []
    for oc in ocorrencias:
        if oc.latitude is None or oc.longitude is None:
            continue
        try:
            lat = float(oc.latitude)
            lng = float(oc.longitude)
        except (TypeError, ValueError):
            continue
        pontos.append({
            'id': oc.id,
            'descricao': oc.descricao or '',
            'categoria': oc.categoria or '',
            'categoria_label': oc.get_categoria_display(),
            'status': oc.status or '',
            'status_label': oc.get_status_display(),
            'prefeitura': str(oc.prefeitura) if getattr(oc, 'prefeitura_id', None) else '',
            'secretaria': str(oc.secretaria) if getattr(oc, 'secretaria_id', None) else '',
            'cep': oc.cep or '',
            'data': oc.date_created.strftime('%d/%m/%Y') if oc.date_created else '',
            'latitude': lat,
            'longitude': lng,
        })
    return pontos

def _ocorrencia_duplicada(ocorrencia, janela_segundos=10):
    """Impede duplicidade por duplo clique ou refresh/reenvio do POST."""
    limite = timezone.now() - timedelta(seconds=janela_segundos)
    qs = Ocorrencia.objects.filter(
        descricao=(ocorrencia.descricao or '').strip(),
        categoria=ocorrencia.categoria,
        prefeitura=ocorrencia.prefeitura,
        cep=ocorrencia.cep or '',
        latitude=ocorrencia.latitude,
        longitude=ocorrencia.longitude,
        anonima=ocorrencia.anonima,
        date_created__gte=limite,
    )
    if ocorrencia.anonima or ocorrencia.usuario_id is None:
        qs = qs.filter(usuario__isnull=True)
    else:
        qs = qs.filter(usuario=ocorrencia.usuario)
    return qs.exists()


# ---------------------------------------------------------------------------
# Páginas públicas
# ---------------------------------------------------------------------------

def landing_page(request):
    stats = {
        'prefeituras': Prefeitura.objects.count(),
        'secretarias': Secretaria.objects.count(),
        'ocorrencias': Ocorrencia.objects.count(),
        'categorias':  len(CategoriaOcorrencia.choices),
    }
    return render(request, 'frontend/landing.html', {'stats': stats})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user   = form.cleaned_data['user']
        perfil = _perfil(user)
        login(request, user)
        if perfil in ('prefeitura', 'secretaria') and getattr(user, 'must_change_password', False):
            messages.warning(request, 'Por segurança, você precisa criar uma nova senha antes de continuar.')
            return redirect('frontend:alterar_senha')
        messages.success(request, 'Login realizado com sucesso.')
        return redirect('frontend:dashboard')
    return render(request, 'frontend/login.html', {
        'form':       form,
        'titulo':     'Bem-vindo de volta',
        'subtitulo':  'Acesse sua conta',
        'botao':      'Entrar',
        'extra_url':  'frontend:cadastro_usuario',
        'extra_link': 'Não tem conta? Cadastre-se',
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('frontend:landing')


@require_http_methods(['GET', 'POST'])
def cadastro_usuario_view(request):
    form = UsuarioCadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário cadastrado com sucesso. Faça login para continuar.')
        return redirect('frontend:login')
    return render(request, 'frontend/cadastro_usuario.html', {
        'form':       form,
        'titulo':     'Criar sua conta',
        'subtitulo':  'Cadastro de cidadão',
        'botao':      'Cadastrar',
        'extra_url':  'frontend:login',
        'extra_link': 'Já tem conta? Faça login',
    })


@require_http_methods(['GET', 'POST'])
def ocorrencia_anonima_view(request):
    form    = OcorrenciaForm(request.POST or None, request.FILES or None, anonimo=True)
    enviado = request.GET.get('enviado') == '1'
    if request.method == 'POST' and form.is_valid():
        oc          = form.save(commit=False)
        oc.anonima  = True
        oc.usuario  = None

        # Vincula automaticamente à secretaria responsável pela categoria
        try:
            oc.secretaria = Secretaria.objects.get(
                prefeitura=oc.prefeitura,
                categoria=oc.categoria
            )
        except Secretaria.DoesNotExist:
            oc.secretaria = None

        if _ocorrencia_duplicada(oc):
            messages.warning(request, 'Essa ocorrência já foi enviada. A duplicidade foi evitada.')
        else:
            oc.save()
            form.save_fotos(oc)
            messages.success(request, 'Ocorrência enviada com sucesso.')

        return redirect(f"{reverse('frontend:ocorrencia_anonima')}?enviado=1")

    return render(request, 'frontend/ocorrencia_anonima.html', {'form': form, 'enviado': enviado})


# ---------------------------------------------------------------------------
# Dashboard — roteador de perfil
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    perfil = _perfil(request.user)
    if perfil == 'admin':
        return _dashboard_admin(request)
    if perfil == 'prefeitura':
        return _dashboard_prefeitura(request)
    if perfil == 'secretaria':
        return _dashboard_secretaria(request)
    return _dashboard_usuario(request)


# ---------------------------------------------------------------------------
# Dashboard Admin
# ---------------------------------------------------------------------------

def _dashboard_admin(request):
    STATUS_CHOICES = StatusOcorrencia.choices

    ocorrencias = Ocorrencia.objects.select_related('prefeitura', 'secretaria').order_by('-date_created')

    status_filtro = request.GET.get('status')
    pref_filtro   = request.GET.get('prefeitura')
    if status_filtro:
        ocorrencias = ocorrencias.filter(status=status_filtro)
    if pref_filtro:
        ocorrencias = ocorrencias.filter(prefeitura_id=pref_filtro)

    context = {
        'perfil':         'admin',
        'ocorrencias':    ocorrencias[:100],
        'total':          Ocorrencia.objects.count(),
        'abertas':        Ocorrencia.objects.filter(status='AB').count(),
        'em_andamento':   Ocorrencia.objects.filter(status__in=['EA', 'AT']).count(),
        'finalizadas':    Ocorrencia.objects.filter(status='RE').count(),
        'prefeituras':    Prefeitura.objects.all(),
        'status_choices': STATUS_CHOICES,
        'status_filtro':  status_filtro,
        'pref_filtro':    pref_filtro,
    }
    return render(request, 'frontend/dashboard_admin.html', context)


# ---------------------------------------------------------------------------
# Dashboard Cidadão
# ---------------------------------------------------------------------------

def _dashboard_usuario(request):
    user = request.user
    form = OcorrenciaForm(request.POST or None, request.FILES or None, anonimo=True)
    if request.method == 'POST' and form.is_valid():
        oc = form.save(commit=False)
        oc.usuario = None if oc.anonima else user

        # Vincula automaticamente à secretaria responsável pela categoria
        try:
            oc.secretaria = Secretaria.objects.get(
                prefeitura=oc.prefeitura,
                categoria=oc.categoria
            )
        except Secretaria.DoesNotExist:
            oc.secretaria = None

        if _ocorrencia_duplicada(oc):
            messages.warning(request, 'Essa ocorrência já foi registrada. A duplicidade foi evitada.')
        else:
            oc.save()
            form.save_fotos(oc)
            messages.success(request, 'Ocorrência registrada com sucesso!')

        return redirect('frontend:dashboard')

    minhas = Ocorrencia.objects.filter(usuario=user).select_related(
        'prefeitura', 'secretaria'
    ).order_by('-date_created')

    context = {
        'perfil':            'usuario',
        'form':              form,
        'minhas_ocorrencias': minhas,
        'ocorrencias_mapa':  _ocorrencias_mapa_payload(minhas),
        'total':             minhas.count(),
        'abertas':           minhas.filter(status='AB').count(),
        'em_andamento':      minhas.filter(status__in=['EA', 'AT']).count(),
        'finalizadas':       minhas.filter(status='RE').count(),
    }
    return render(request, 'frontend/dashboard_usuario.html', context)


# ---------------------------------------------------------------------------
# Dashboard Prefeitura
# ---------------------------------------------------------------------------

def _dashboard_prefeitura(request):
    user      = request.user
    prefeitura = user.prefeitura

    form_sec = SecretariaForm(
        request.POST if 'cadastrar_secretaria' in request.POST else None,
        prefeitura=prefeitura,
    )
    if request.method == 'POST' and 'cadastrar_secretaria' in request.POST and form_sec.is_valid():
        sec            = form_sec.save(commit=False)
        sec.prefeitura = prefeitura
        sec.save()
        messages.success(request, 'Secretaria cadastrada com sucesso.')
        return redirect('frontend:dashboard')

    secretarias  = Secretaria.objects.filter(prefeitura=prefeitura).order_by('name')
    ocorrencias  = Ocorrencia.objects.filter(prefeitura=prefeitura).select_related(
        'secretaria'
    ).order_by('-date_created')

    sec_filtro    = request.GET.get('secretaria')
    status_filtro = request.GET.get('status')
    if sec_filtro:
        ocorrencias = ocorrencias.filter(secretaria_id=sec_filtro)
    if status_filtro:
        ocorrencias = ocorrencias.filter(status=status_filtro)

    # Resumo por categoria usando os choices (sem FK para Categoria)
    cat_map = dict(CategoriaOcorrencia.choices)
    por_categoria = (
        Ocorrencia.objects.filter(prefeitura=prefeitura)
        .values('categoria')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    categorias_resumo = [
        {'nome': cat_map.get(c['categoria'], c['categoria']), 'total': c['total']}
        for c in por_categoria
    ]

    context = {
        'perfil':            'prefeitura',
        'prefeitura':        prefeitura,
        'secretarias':       secretarias,
        'form_sec':          form_sec,
        'ocorrencias':       ocorrencias[:50],
        'ocorrencias_mapa':  _ocorrencias_mapa_payload(ocorrencias),
        'total':             Ocorrencia.objects.filter(prefeitura=prefeitura).count(),
        'abertas':           Ocorrencia.objects.filter(prefeitura=prefeitura, status='AB').count(),
        'em_andamento':      Ocorrencia.objects.filter(prefeitura=prefeitura, status__in=['EA', 'AT']).count(),
        'finalizadas':       Ocorrencia.objects.filter(prefeitura=prefeitura, status='RE').count(),
        'categorias_resumo': categorias_resumo,
        'sec_filtro':        sec_filtro,
        'status_filtro':     status_filtro,
        'status_choices':    StatusOcorrencia.choices,
    }
    return render(request, 'frontend/dashboard_prefeitura.html', context)


# ---------------------------------------------------------------------------
# Dashboard Secretaria
# ---------------------------------------------------------------------------

def _dashboard_secretaria(request):
    secretaria  = request.user.secretaria_vinculada
    ocorrencias = Ocorrencia.objects.filter(secretaria=secretaria).select_related(
        'prefeitura'
    ).order_by('-date_created')

    status_filtro = request.GET.get('status')
    if status_filtro:
        ocorrencias = ocorrencias.filter(status=status_filtro)

    STATUS_VALIDOS = dict(StatusOcorrencia.choices)
    if request.method == 'POST' and 'ocorrencia_id' in request.POST:
        oc_id      = request.POST.get('ocorrencia_id')
        novo_status = request.POST.get('novo_status')
        try:
            oc = Ocorrencia.objects.get(pk=oc_id, secretaria=secretaria)
            if novo_status in STATUS_VALIDOS:
                oc.status = novo_status
                oc.save()
                messages.success(request, 'Status atualizado.')
        except Ocorrencia.DoesNotExist:
            messages.error(request, 'Ocorrência não encontrada.')
        return redirect('frontend:dashboard')

    por_status = {
        row['status']: row['total']
        for row in Ocorrencia.objects.filter(secretaria=secretaria)
        .values('status').annotate(total=Count('id'))
    }

    # Exibe label da categoria a partir dos choices
    cat_map = dict(CategoriaOcorrencia.choices)
    categoria_display = cat_map.get(secretaria.categoria, secretaria.categoria or '—')

    context = {
        'perfil':             'secretaria',
        'secretaria':         secretaria,
        'ocorrencias':        ocorrencias,
        'ocorrencias_mapa':   _ocorrencias_mapa_payload(ocorrencias),
        'total':              Ocorrencia.objects.filter(secretaria=secretaria).count(),
        'abertas':            por_status.get('AB', 0),
        'em_andamento':       por_status.get('EA', 0) + por_status.get('AT', 0),
        'finalizadas':        por_status.get('RE', 0),
        'status_filtro':      status_filtro,
        'status_choices':     StatusOcorrencia.choices,
        'categoria_display':  categoria_display,
    }
    return render(request, 'frontend/dashboard_secretaria.html', context)


# ---------------------------------------------------------------------------
# Troca de senha obrigatória (primeiro login de prefeitura/secretaria)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def alterar_senha_view(request):
    user   = request.user
    perfil = _perfil(user)

    if perfil not in ('prefeitura', 'secretaria'):
        return redirect('frontend:dashboard')
    if not getattr(user, 'must_change_password', False):
        return redirect('frontend:dashboard')

    form = AlterarSenhaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['nova_senha'])
        user.must_change_password = False
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Senha alterada com sucesso! Bem-vindo(a).')
        return redirect('frontend:dashboard')

    return render(request, 'frontend/alterar_senha.html', {'form': form, 'perfil': perfil})


# ---------------------------------------------------------------------------
# CRUD de Prefeituras (admin)
# ---------------------------------------------------------------------------

@login_required
def prefeituras_view(request):
    form           = PrefeituraForm(request.POST or None)
    senha_gerada   = None
    email_gerado   = None
    if request.method == 'POST' and form.is_valid():
        form.save()
        if form._senha_temporaria:
            senha_gerada = form._senha_temporaria
            email_gerado = form.instance.email
        else:
            messages.success(request, 'Prefeitura salva com sucesso.')
            return redirect('frontend:prefeituras')
    return render(request, 'frontend/prefeituras.html', {
        'form':          PrefeituraForm(),
        'items':         Prefeitura.objects.prefetch_related('secretarias').all(),
        'senha_gerada':  senha_gerada,
        'email_gerado':  email_gerado,
    })


@login_required
def prefeitura_editar_view(request, pk):
    prefeitura = get_object_or_404(Prefeitura, pk=pk)
    form       = PrefeituraForm(request.POST or None, instance=prefeitura)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Prefeitura atualizada com sucesso.')
        return redirect('frontend:prefeituras')
    return render(request, 'frontend/prefeituras.html', {
        'form':     form,
        'items':    Prefeitura.objects.prefetch_related('secretarias').all(),
        'editando': prefeitura,
    })


@login_required
def prefeitura_excluir_view(request, pk):
    prefeitura = get_object_or_404(Prefeitura, pk=pk)
    if request.method == 'POST':
        for sec in prefeitura.secretarias.select_related('usuario').all():
            if sec.usuario:
                sec.usuario.is_active = False
                sec.usuario.save(update_fields=['is_active'])
            sec.delete()
        if prefeitura.usuario:
            prefeitura.usuario.is_active = False
            prefeitura.usuario.save(update_fields=['is_active'])
        prefeitura.delete()
        messages.success(request, 'Prefeitura e secretarias vinculadas excluídas com sucesso.')
    return redirect('frontend:prefeituras')


# ---------------------------------------------------------------------------
# CRUD de Secretarias (admin / prefeitura)
# ---------------------------------------------------------------------------

@login_required
def secretarias_view(request):
    form           = SecretariaForm(request.POST or None)
    senha_gerada   = None
    email_gerado   = None
    if request.method == 'POST' and form.is_valid():
        form.save()
        if form._senha_temporaria:
            senha_gerada = form._senha_temporaria
            email_gerado = form.instance.email
        else:
            messages.success(request, 'Secretaria salva com sucesso.')
            return redirect('frontend:secretarias')
    return render(request, 'frontend/secretarias.html', {
        'form':         SecretariaForm(),
        'items':        Secretaria.objects.select_related('prefeitura'),
        'senha_gerada': senha_gerada,
        'email_gerado': email_gerado,
    })


@login_required
def secretaria_editar_view(request, pk):
    secretaria = get_object_or_404(Secretaria, pk=pk)
    form       = SecretariaForm(request.POST or None, instance=secretaria)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Secretaria atualizada com sucesso.')
        return redirect('frontend:secretarias')
    return render(request, 'frontend/secretarias.html', {
        'form':     form,
        'items':    Secretaria.objects.select_related('prefeitura'),
        'editando': secretaria,
    })


@login_required
def secretaria_excluir_view(request, pk):
    secretaria = get_object_or_404(Secretaria, pk=pk)
    if request.method == 'POST':
        if secretaria.usuario:
            secretaria.usuario.is_active = False
            secretaria.usuario.save(update_fields=['is_active'])
        secretaria.delete()
        messages.success(request, 'Secretaria excluída com sucesso.')
    return redirect('frontend:secretarias')
