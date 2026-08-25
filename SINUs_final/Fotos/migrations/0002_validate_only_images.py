# Generated manually to add upload validation for Fotos.arquivo.

from django.db import migrations, models
import Fotos.validators


class Migration(migrations.Migration):

    dependencies = [
        ('Fotos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fotos',
            name='arquivo',
            field=models.ImageField(
                upload_to='ocorrencias/fotos/',
                validators=[Fotos.validators.validate_image_file],
            ),
        ),
    ]
