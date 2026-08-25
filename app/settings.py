"""
Django settings for PI_SINUS_MERGED
Backend (API REST) + Frontend (Django Templates) unificados.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-!sig^)-nh6cj-xy+o=k_xn+owa3@*0o8e(gjmw%g(w$0sj2a#)'

DEBUG = True

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'Usuario.Usuario'

# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceiros
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'localflavor',
    'phonenumber_field',

    # ── Backend (API) ──────────────────────────────────────────────────────
    'core',           # choices globais (CategoriaOcorrencia)
    'authentication', # config de autenticação JWT
    'Usuario',
    'Prefeitura',
    'Secretaria',
    'Ocorrencias',
    'Fotos',
    'Administracao',

    # ── Frontend (Templates Django) ────────────────────────────────────────
    'frontend',
]

# ---------------------------------------------------------------------------
# REST Framework / JWT
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # TokenAuthentication mantida porque /api/login/ retorna token DRF.
        'rest_framework.authentication.TokenAuthentication',
        # Session auth mantida para o frontend Django Templates.
        'rest_framework.authentication.SessionAuthentication',
    ),
}

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

# ---------------------------------------------------------------------------
# Templates — busca em todos os apps (APP_DIRS=True)
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# Validadores de senha
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'pt-br'
TIME_ZONE     = 'America/Sao_Paulo'
USE_I18N      = True
USE_TZ        = True

# ---------------------------------------------------------------------------
# Arquivos estáticos e de mídia
# ---------------------------------------------------------------------------

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL  = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Redirecionamentos do frontend (sessão Django)
# ---------------------------------------------------------------------------

LOGIN_URL           = 'frontend:login'
LOGIN_REDIRECT_URL  = 'frontend:dashboard'
LOGOUT_REDIRECT_URL = 'frontend:landing'
