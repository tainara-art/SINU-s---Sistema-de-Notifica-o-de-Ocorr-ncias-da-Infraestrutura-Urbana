from django.contrib import admin
from Ocorrencias.models import Ocorrencia

class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('categoria', 'descricao','status',)
    search_fields = ('status', 'descricao',)
    list_filter = ('status',)
    
admin.site.register(Ocorrencia, OcorrenciaAdmin)
