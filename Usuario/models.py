# Usuario/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.br.models import BRPostalCodeField


# ---------------------------------------------------------------------------
# Manager customizado - obrigatorio quando username e removido do AbstractUser
# ---------------------------------------------------------------------------

class UsuarioManager(BaseUserManager):
    """Manager compativel com usuario customizado sem campo username."""

    def _criar_usuario(self, email, password, **extra_fields):
        # Compatibilidade defensiva: se algum ponto antigo do projeto ainda
        # enviar username, usa esse valor como e-mail e remove o campo invalido.
        email = email or extra_fields.pop('username', None)
        extra_fields.pop('username', None)

        if not email:
            raise ValueError('O e-mail e obrigatorio.')

        email = self.normalize_email(email)

        # Valores minimos para permitir createsuperuser sem campos extras.
        extra_fields.setdefault('name', extra_fields.get('name') or email.split('@')[0])
        extra_fields.setdefault('phone', extra_fields.get('phone') or '+5511000000000')
        extra_fields.setdefault('cep', extra_fields.get('cep') or '01310-100')

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._criar_usuario(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuario precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuario precisa ter is_superuser=True.')

        return self._criar_usuario(email, password, **extra_fields)


# ---------------------------------------------------------------------------
# Model de usuario customizado
# ---------------------------------------------------------------------------

class Usuario(AbstractUser):
    """
    Usuario customizado do sistema SINUS.

    - username removido; e-mail e o campo de login (USERNAME_FIELD).
    - must_change_password: flag usada pelo frontend para forcar troca de
      senha no primeiro acesso de prefeitura/secretaria criados pelo admin.
    - tipo_usuario: informativo, usado pela API para retornar o perfil no login.
    """

    username = None

    name                 = models.CharField(max_length=100)
    email                = models.EmailField(max_length=254, unique=True)
    phone                = PhoneNumberField(region='BR')
    cep                  = BRPostalCodeField()
    tipo_usuario         = models.CharField(max_length=20, default='USUARIO')
    must_change_password = models.BooleanField(
        default=False,
        help_text='Se True, o usuário será obrigado a alterar a senha no próximo login.',
    )

    objects = UsuarioManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name or self.email
