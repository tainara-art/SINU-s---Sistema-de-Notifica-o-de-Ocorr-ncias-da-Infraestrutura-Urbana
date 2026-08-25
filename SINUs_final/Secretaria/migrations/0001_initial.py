# Secretaria/migrations/0001_initial.py — migration consolidada
import django.db.models.deletion
import localflavor.br.models
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Prefeitura', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Secretaria',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',       models.CharField(max_length=100)),
                ('email',      models.EmailField(max_length=100, unique=True)),
                ('phone',      phonenumber_field.modelfields.PhoneNumberField(max_length=128, region='BR')),
                ('cep',        localflavor.br.models.BRPostalCodeField(max_length=9)),
                ('categoria',  models.CharField(blank=True, null=True, max_length=2,
                                   choices=[('SB','Saneamento Básico'),('PV','Pavimentação e Vias'),
                                            ('IP','Iluminação Pública'),('LU','Limpeza Urbana'),
                                            ('AS','Animais em Risco'),('AP','Arborização e Praças'),
                                            ('ST','Sinalização de Trânsito'),('OS','Obras e Serviços')])),
                ('prefeitura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                   related_name='secretarias', to='Prefeitura.prefeitura')),
                ('usuario',    models.OneToOneField(blank=True, null=True,
                                   on_delete=django.db.models.deletion.CASCADE,
                                   related_name='secretaria_vinculada', to=settings.AUTH_USER_MODEL)),
            ],
            options={'unique_together': {('prefeitura', 'categoria')}},
        ),
    ]
