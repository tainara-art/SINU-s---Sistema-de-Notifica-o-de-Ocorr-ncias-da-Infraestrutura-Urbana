from django.db import models

class AdminPrefeitura(models.Model):
    usuario    = models.OneToOneField(
                     'Usuario.Usuario',
                     on_delete=models.CASCADE,
                     related_name='admin_prefeitura')
    prefeitura = models.ForeignKey(
                     'Prefeitura.Prefeitura',
                     on_delete=models.CASCADE,
                     related_name='admins')
    cidade     = models.CharField(max_length=100)
    estado     = models.CharField(max_length=2)

    def __str__(self):
        return f'Admin Prefeitura: {self.usuario.name}'


class AdminSecretaria(models.Model):
    usuario    = models.OneToOneField(
                     'Usuario.Usuario',
                     on_delete=models.CASCADE,
                     related_name='admin_secretaria')
    secretaria = models.ForeignKey(
                     'Secretaria.Secretaria',
                     on_delete=models.CASCADE,
                     related_name='admins')
    nome       = models.CharField(max_length=100)

    def __str__(self):
        return f'Admin Secretaria: {self.usuario.name}'
