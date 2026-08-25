# Ocorrencias/migrations/0001_initial.py — migration consolidada
import django.db.models.deletion
import localflavor.br.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Prefeitura', '0001_initial'),
        ('Secretaria', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ocorrencia',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao',    models.CharField(max_length=450)),
                ('cep',          localflavor.br.models.BRPostalCodeField(blank=True, default='', max_length=9)),
                ('latitude',     models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude',    models.DecimalField(decimal_places=6, max_digits=9)),
                ('status',       models.CharField(
                                     max_length=2, default='AB',
                                     choices=[('AB','Aberta'),('EA','Em Análise'),('AT','Em Atendimento'),('RE','Resolvida')])),
                ('prioridade',   models.CharField(
                                     max_length=1, default='B',
                                     choices=[('B','Baixa'),('M','Média'),('A','Alta'),('U','Urgente')])),
                ('categoria',    models.CharField(
                                     max_length=2,
                                     choices=[('SB','Saneamento Básico'),('PV','Pavimentação e Vias'),
                                              ('IP','Iluminação Pública'),('LU','Limpeza Urbana'),
                                              ('AS','Animais em Risco'),('AP','Arborização e Praças'),
                                              ('ST','Sinalização de Trânsito'),('OS','Obras e Serviços')])),
                ('anonima',      models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_update',  models.DateTimeField(auto_now=True)),
                ('prefeitura',   models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT,
                                     related_name='ocorrencias', to='Prefeitura.prefeitura')),
                ('secretaria',   models.ForeignKey(blank=True, null=True,
                                     on_delete=django.db.models.deletion.SET_NULL,
                                     related_name='ocorrencias', to='Secretaria.secretaria')),
                ('usuario',      models.ForeignKey(blank=True, null=True,
                                     on_delete=django.db.models.deletion.SET_NULL,
                                     related_name='ocorrencias', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoStatus',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_anterior', models.CharField(blank=True, max_length=2,
                                        choices=[('AB','Aberta'),('EA','Em Análise'),('AT','Em Atendimento'),('RE','Resolvida')])),
                ('status_novo',     models.CharField(max_length=2,
                                        choices=[('AB','Aberta'),('EA','Em Análise'),('AT','Em Atendimento'),('RE','Resolvida')])),
                ('observacao',      models.TextField(blank=True)),
                ('alterado_em',     models.DateTimeField(auto_now_add=True)),
                ('ocorrencia',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                        related_name='historico', to='Ocorrencias.ocorrencia')),
                ('responsavel',     models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                        related_name='historicos', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-alterado_em']},
        ),
    ]
