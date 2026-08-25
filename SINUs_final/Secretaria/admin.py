from django.contrib import admin
from Secretaria.models import Secretaria

class SecretariaAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'cep',)
    search_fields = ('name', )

admin.site.register(Secretaria, SecretariaAdmin)