from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.br.models import BRPostalCodeField
from core.choices import CategoriaOcorrencia as CategoriaSecretaria

class Secretaria(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField(max_length=100, unique=True)
    phone      = PhoneNumberField(region='BR')
    cep        = BRPostalCodeField()
    usuario    = models.OneToOneField(
        'Usuario.Usuario',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='secretaria_vinculada'
    )
    categoria  = models.CharField(
        max_length=2,
        choices=CategoriaSecretaria.choices,
        null=True, blank=True
    )
    prefeitura = models.ForeignKey(
        'Prefeitura.Prefeitura',
        on_delete=models.CASCADE,
        related_name='secretarias'
    )

    class Meta:
        unique_together = [['prefeitura', 'categoria']]  # RN03

    def __str__(self):
        return self.name
