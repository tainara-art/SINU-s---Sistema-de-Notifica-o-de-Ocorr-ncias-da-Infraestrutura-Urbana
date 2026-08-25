# frontend/forms.py
from django import forms
from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string

from Usuario.models     import Usuario
from Prefeitura.models  import Prefeitura
from Secretaria.models  import Secretaria
from Ocorrencias.models import Ocorrencia
from Fotos.models       import Fotos
from Fotos.validators   import MAX_FOTOS_POR_OCORRENCIA, validate_image_file
from core.choices       import CategoriaOcorrencia


# ---------------------------------------------------------------------------
# Mixin Bootstrap
# ---------------------------------------------------------------------------

class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            current = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{current} form-control'.strip()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginForm(forms.Form):
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Sua senha'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email    = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if not (email and password):
            return cleaned_data

        try:
            usuario_db = Usuario.objects.get(email=email)
            if not usuario_db.is_active:
                if Prefeitura.objects.filter(usuario=usuario_db).exists():
                    raise forms.ValidationError('Prefeitura não encontrada. O acesso foi removido.')
                elif Secretaria.objects.filter(usuario=usuario_db).exists():
                    raise forms.ValidationError('Secretaria não encontrada. O acesso foi removido.')
                else:
                    raise forms.ValidationError('Esta conta foi desativada.')
        except Usuario.DoesNotExist:
            raise forms.ValidationError('E-mail ou senha inválidos.')

        user = authenticate(username=email, password=password)
        if not user:
            raise forms.ValidationError('E-mail ou senha inválidos.')

        cleaned_data['user'] = user
        return cleaned_data


# ---------------------------------------------------------------------------
# Alterar senha
# ---------------------------------------------------------------------------

class AlterarSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres', 'autofocus': True}),
        min_length=8,
    )
    confirmar_senha = forms.CharField(
        label='Confirmar nova senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a nova senha'}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('nova_senha') != cleaned.get('confirmar_senha'):
            self.add_error('confirmar_senha', 'As senhas não conferem.')
        return cleaned


# ---------------------------------------------------------------------------
# Cadastro de cidadão
# ---------------------------------------------------------------------------

class UsuarioCadastroForm(BaseStyledForm):
    password         = forms.CharField(label='Senha',           widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model  = Usuario
        fields = ['name', 'email', 'phone', 'cep']
        labels = {'name': 'Nome completo', 'email': 'E-mail', 'phone': 'Telefone', 'cep': 'CEP'}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            self.add_error('password_confirm', 'As senhas não conferem.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.tipo_usuario = 'USUARIO'
        if commit:
            user.save()
        return user


# ---------------------------------------------------------------------------
# Upload múltiplo de imagens
# ---------------------------------------------------------------------------

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError(self.error_messages['required'], code='required')
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleImageField, self).clean(item, initial) for item in data]


# ---------------------------------------------------------------------------
# Ocorrência — BUG 3 CORRIGIDO: 'fotos' removido de Meta.fields
# ---------------------------------------------------------------------------

class OcorrenciaForm(BaseStyledForm):
    # Campo extra — NÃO vai em Meta.fields pois não é coluna do model
    fotos = MultipleImageField(
        label='Foto da ocorrência',
        required=True,
        help_text=f'Envie até {MAX_FOTOS_POR_OCORRENCIA} fotos (JPG, JPEG, PNG, WEBP, GIF, JFIF).',
        widget=MultipleFileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp,.gif,.jfif',
            'multiple': True,
        }),
    )

    class Meta:
        model  = Ocorrencia
        # 'fotos' não está aqui — é campo extra acima
        fields = ['descricao', 'categoria', 'prefeitura', 'cep', 'latitude', 'longitude', 'anonima']
        labels = {
            'descricao':  'Descrição',
            'categoria':  'Categoria',
            'prefeitura': 'Prefeitura (cidade)',
            'cep':        'CEP do local',
            'latitude':   'Latitude',
            'longitude':  'Longitude',
            'anonima':    'Enviar anonimamente',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descreva o problema com detalhes...'}),
            'cep':       forms.TextInput(attrs={
                'readonly':    'readonly',
                'placeholder': 'Preenchido automaticamente pelo mapa',
                'class':       'js-map-cep',
                'title':       'O CEP é preenchido automaticamente ao selecionar a localização no mapa.',
            }),
            'latitude':  forms.HiddenInput(attrs={'class': 'js-map-latitude'}),
            'longitude': forms.HiddenInput(attrs={'class': 'js-map-longitude'}),
            'anonima':   forms.CheckboxInput(),
        }

    def __init__(self, *args, anonimo=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cep'].required = True
        if anonimo:
            self.fields.pop('anonima', None)

    def clean(self):
        cleaned = super().clean()
        latitude = cleaned.get('latitude')
        longitude = cleaned.get('longitude')

        if latitude is None or longitude is None:
            raise forms.ValidationError('Selecione a localização da ocorrência no mapa antes de enviar.')

        return cleaned

    def clean_fotos(self):
        fotos = self.cleaned_data.get('fotos') or []
        if len(fotos) > MAX_FOTOS_POR_OCORRENCIA:
            raise forms.ValidationError(f'Envie no máximo {MAX_FOTOS_POR_OCORRENCIA} fotos por ocorrência.')
        for foto in fotos:
            validate_image_file(foto)
        return fotos

    def save_fotos(self, ocorrencia):
        for foto in self.cleaned_data.get('fotos') or []:
            Fotos.objects.create(ocorrencia=ocorrencia, arquivo=foto)


# ---------------------------------------------------------------------------
# Helper — BUG 4 CORRIGIDO: parâmetro tipo= agora funciona corretamente
# ---------------------------------------------------------------------------

def _criar_usuario_automatico(name, email, phone='+5511000000000', cep='01310100', tipo='USUARIO'):
    """Cria um Usuario com senha temporária. Retorna (usuario, senha_temporaria)."""
    senha = get_random_string(12)
    user  = Usuario(
        email=email,
        name=name,
        phone=phone,
        cep=cep,
        tipo_usuario=tipo,          # usa o tipo passado, sem sobrescrever depois
        must_change_password=True,
    )
    user.set_password(senha)
    user.save()
    return user, senha


# ---------------------------------------------------------------------------
# Prefeitura
# ---------------------------------------------------------------------------

class PrefeituraForm(BaseStyledForm):
    class Meta:
        model  = Prefeitura
        fields = ['name', 'company_name', 'trade_name', 'cnpj', 'email', 'cep']
        labels = {
            'name':         'Nome da prefeitura',
            'company_name': 'Razão social',
            'trade_name':   'Nome fantasia',
            'cnpj':         'CNPJ',
            'email':        'E-mail institucional',
            'cep':          'CEP',
        }

    def save(self, commit=True):
        prefeitura = super().save(commit=False)
        self._senha_temporaria = None
        if not prefeitura.usuario_id and not Usuario.objects.filter(email=prefeitura.email).exists():
            user, senha = _criar_usuario_automatico(
                name=prefeitura.name,
                email=prefeitura.email,
                cep=str(prefeitura.cep),
                tipo='PREFEITURA',
            )
            prefeitura.usuario     = user
            self._senha_temporaria = senha
        if commit:
            prefeitura.save()
        return prefeitura


# ---------------------------------------------------------------------------
# Secretaria
# ---------------------------------------------------------------------------

class SecretariaForm(BaseStyledForm):
    categoria = forms.ChoiceField(
        choices=[('', '— Selecione uma categoria —')] + list(CategoriaOcorrencia.choices),
        label='Categoria atendida',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, prefeitura=None, **kwargs):
        super().__init__(*args, **kwargs)
        if prefeitura is not None:
            self.fields.pop('prefeitura', None)

    class Meta:
        model  = Secretaria
        fields = ['name', 'email', 'phone', 'cep', 'categoria', 'prefeitura']
        labels = {
            'name':       'Nome da secretaria',
            'email':      'E-mail institucional',
            'phone':      'Telefone',
            'cep':        'CEP',
            'prefeitura': 'Prefeitura vinculada',
        }

    def save(self, commit=True):
        secretaria = super().save(commit=False)
        self._senha_temporaria = None
        if not secretaria.usuario_id and not Usuario.objects.filter(email=secretaria.email).exists():
            user, senha = _criar_usuario_automatico(
                name=secretaria.name,
                email=secretaria.email,
                phone=str(secretaria.phone),
                cep=str(secretaria.cep),
                tipo='SECRETARIA',
            )
            secretaria.usuario     = user
            self._senha_temporaria = senha
        if commit:
            secretaria.save()
        return secretaria
