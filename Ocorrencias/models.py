import os
from django.db import models
from django.core.exceptions import ValidationError
from localflavor.br.models import BRPostalCodeField
from core.choices import CategoriaOcorrencia

EXTENSOES_PERMITIDAS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.jfif']

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in EXTENSOES_PERMITIDAS:
        raise ValidationError(
            f'Tipo de arquivo não permitido. Envie somente fotos nos formatos: {", ".join(EXTENSOES_PERMITIDAS)}'
        )

class StatusOcorrencia(models.TextChoices):
    ABERTA         = 'AB', 'Aberta'
    EM_ANALISE     = 'EA', 'Em Análise'
    EM_ATENDIMENTO = 'AT', 'Em Atendimento'
    RESOLVIDA      = 'RE', 'Resolvida'

class PrioridadeOcorrencia(models.TextChoices):
    BAIXA   = 'B', 'Baixa'
    MEDIA   = 'M', 'Média'
    ALTA    = 'A', 'Alta'
    URGENTE = 'U', 'Urgente'

class Ocorrencia(models.Model):
    descricao  = models.CharField(max_length=450)
    cep        = BRPostalCodeField(blank=True, default='')
    latitude   = models.DecimalField(max_digits=9, decimal_places=6)
    longitude  = models.DecimalField(max_digits=9, decimal_places=6)
    status     = models.CharField(
                     max_length=2,
                     choices=StatusOcorrencia.choices,
                     default=StatusOcorrencia.ABERTA)
    prioridade = models.CharField(
                     max_length=1,
                     choices=PrioridadeOcorrencia.choices,
                     default=PrioridadeOcorrencia.BAIXA)
    categoria  = models.CharField(
                     max_length=2,
                     choices=CategoriaOcorrencia.choices)
    anonima    = models.BooleanField(default=False)

    usuario    = models.ForeignKey(
                     'Usuario.Usuario',
                     on_delete=models.SET_NULL,
                     null=True, blank=True,
                     related_name='ocorrencias')
    prefeitura = models.ForeignKey(
                     'Prefeitura.Prefeitura',
                     on_delete=models.RESTRICT,
                     related_name='ocorrencias')
    secretaria = models.ForeignKey(
                     'Secretaria.Secretaria',
                     on_delete=models.SET_NULL,
                     null=True, blank=True,
                     related_name='ocorrencias')

    date_created = models.DateTimeField(auto_now_add=True)
    date_update  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_categoria_display()} - {self.get_status_display()}'


class HistoricoStatus(models.Model):
    ocorrencia      = models.ForeignKey(
                          Ocorrencia,
                          on_delete=models.CASCADE,
                          related_name='historico')
    status_anterior = models.CharField(
                          max_length=2,
                          choices=StatusOcorrencia.choices,
                          blank=True)
    status_novo     = models.CharField(
                          max_length=2,
                          choices=StatusOcorrencia.choices)
    observacao      = models.TextField(blank=True)
    responsavel     = models.ForeignKey(
                          'Usuario.Usuario',
                          on_delete=models.SET_NULL,
                          null=True,
                          related_name='historicos')
    alterado_em     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-alterado_em']

    # RN05 — histórico imutável
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Histórico de status é imutável.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Histórico de status não pode ser excluído.')

    def __str__(self):
        return f'Ocorrencia {self.ocorrencia_id}: {self.status_anterior} -> {self.status_novo}'
