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
    # Identificador público e permanente da ocorrência.
    # Exemplo: 202610-OBR-001.
    protocolo = models.CharField(
    max_length=30,
    unique=True,
    null=True,
    blank=True,
    editable=False
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_update  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.get_categoria_display()} - {self.get_status_display()}'


class HistoricoStatus(models.Model):
    """
    Registra as mudanças de status da ocorrência.

    Os registros são históricos e não podem ser
    alterados ou excluídos diretamente.
    """

    ocorrencia = models.ForeignKey(
        Ocorrencia,
        on_delete=models.CASCADE,
        related_name='historico'
    )

    status_anterior = models.CharField(
        max_length=2,
        choices=StatusOcorrencia.choices,
        blank=True
    )

    status_novo = models.CharField(
        max_length=2,
        choices=StatusOcorrencia.choices
    )

    observacao = models.TextField(blank=True)

    responsavel = models.ForeignKey(
        'Usuario.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historicos'
    )

    alterado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-alterado_em']

    # RN05 — histórico imutável.
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                'Histórico de status é imutável.'
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Histórico de status não pode ser excluído.'
        )

    def __str__(self):
        return (
            f'Ocorrencia {self.ocorrencia_id}: '
            f'{self.status_anterior} -> {self.status_novo}'
        )


class SequenciaProtocolo(models.Model):
    """
    Controla a numeração dos protocolos por
    competência (ano/mês) e secretaria.

    Exemplo:
        competencia = 202610
        sigla = OBR
        ultimo_numero = 15

    Próximo protocolo: 202610-OBR-016
    """

    competencia = models.CharField(
        max_length=6
    )

    sigla = models.CharField(
        max_length=3
    )

    ultimo_numero = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['competencia', 'sigla'],
                name='unique_sequencia_protocolo'
            )
        ]

    def __str__(self):
        return f'{self.competencia}-{self.sigla}'


class RegistroProtocolo(models.Model):
    """
    Registra cada ação relevante sobre uma ocorrência.

    Cada registro possui código único, tipo de ação,
    responsável, observação e data de criação.
    """

    class TipoAcao(models.TextChoices):
        CRIACAO = 'CR', 'Criação'
        ENCAMINHAMENTO = 'EN', 'Encaminhamento'
        STATUS = 'ST', 'Mudança de status'
        OBSERVACAO = 'OB', 'Observação'

    class Visibilidade(models.TextChoices):
        PUBLICA = 'PU', 'Pública'
        INTERNA = 'IN', 'Interna'

    ocorrencia = models.ForeignKey(
        Ocorrencia,
        on_delete=models.PROTECT,
        related_name='registros_protocolo'
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )

    tipo_acao = models.CharField(
        max_length=2,
        choices=TipoAcao.choices
    )

    visibilidade = models.CharField(
        max_length=2,
        choices=Visibilidade.choices,
        default=Visibilidade.PUBLICA
    )

    responsavel = models.ForeignKey(
        'Usuario.Usuario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='registros_protocolo'
    )

    observacao = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-criado_em', '-id']

    # RN05 — registros de protocolo imutáveis.
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(
                'Registros de protocolo são imutáveis.'
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Registros de protocolo não podem ser excluídos.'
        )

    def __str__(self):
        return (
            f'{self.codigo} - '
            f'{self.get_tipo_acao_display()}'
        )