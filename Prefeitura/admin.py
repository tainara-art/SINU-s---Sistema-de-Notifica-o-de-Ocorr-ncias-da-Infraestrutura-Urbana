from django.contrib import admin
from Prefeitura.models import Prefeitura

class PrefeituraAdmin(admin.ModelAdmin):
    list_display = ('name', 'email','cep',)
    search_fields = ('name', )

admin.site.register(Prefeitura, PrefeituraAdmin)