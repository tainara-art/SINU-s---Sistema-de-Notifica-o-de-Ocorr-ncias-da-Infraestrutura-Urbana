from django.db import models

from .validators import validate_image_file


class Fotos(models.Model):
    ocorrencia = models.ForeignKey(
        'Ocorrencias.Ocorrencia',
        on_delete=models.CASCADE,
        related_name='fotos_da_ocorrencia'
    )
    arquivo = models.ImageField(
        upload_to='ocorrencias/fotos/',
        validators=[validate_image_file],
    )
    date_send = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto da ocorrência #{self.ocorrencia.id}"
