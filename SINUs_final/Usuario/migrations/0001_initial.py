# Gerado manualmente para refletir o model reconciliado (backend + frontend).
from django.db import migrations, models
import django.utils.timezone
import localflavor.br.models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id',                   models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password',             models.CharField(max_length=128, verbose_name='password')),
                ('last_login',           models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser',         models.BooleanField(default=False)),
                ('first_name',           models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name',            models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff',             models.BooleanField(default=False)),
                ('is_active',            models.BooleanField(default=True)),
                ('date_joined',          models.DateTimeField(default=django.utils.timezone.now)),
                ('name',                 models.CharField(max_length=100)),
                ('email',                models.EmailField(max_length=254, unique=True)),
                ('phone',                phonenumber_field.modelfields.PhoneNumberField(max_length=128, region='BR')),
                ('cep',                  localflavor.br.models.BRPostalCodeField(max_length=9)),
                ('tipo_usuario',         models.CharField(default='USUARIO', max_length=20)),
                ('must_change_password', models.BooleanField(default=False,
                    help_text='Se True, o usuário será obrigado a alterar a senha no próximo login.')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
