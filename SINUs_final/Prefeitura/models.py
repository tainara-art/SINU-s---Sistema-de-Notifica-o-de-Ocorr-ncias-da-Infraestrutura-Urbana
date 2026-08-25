from django.db import models 
from phonenumber_field.modelfields import PhoneNumberField
from localflavor.br.models import BRPostalCodeField, BRCNPJField


class Prefeitura(models.Model):
    name=models.CharField(max_length=100)
    company_name=models.CharField(max_length=100) # razão social
    trade_name=models.CharField(max_length=100) # nome fantasia
    cnpj = BRCNPJField(unique=True) #masked.True salva com pontuação
    email = models.EmailField(max_length=254, unique=True)
    cep = BRPostalCodeField()
    usuario = models.OneToOneField('Usuario.Usuario', on_delete=models.CASCADE, null=True, blank=True)
    

    def __str__(self):
        return self.name