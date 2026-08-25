from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from Usuario.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display = ('email', 'name', 'tipo_usuario', 'phone', 'cep', 'is_staff', 'is_active')
    list_filter = ('tipo_usuario', 'is_staff', 'is_active', 'is_superuser', 'must_change_password')
    search_fields = ('email', 'name', 'phone')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dados pessoais', {'fields': ('name', 'phone', 'cep', 'tipo_usuario')}),
        ('Acesso', {'fields': ('must_change_password', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone', 'cep', 'tipo_usuario', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')
