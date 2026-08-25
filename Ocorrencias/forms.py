from django import forms

from Fotos.validators import validate_image_file


class FotoUploadForm(forms.Form):
    foto = forms.ImageField(
        label='Foto',
        required=True,
        validators=[validate_image_file],
        widget=forms.ClearableFileInput(attrs={
            'accept': '.jpg,.jpeg,.png,.webp,.gif,.jfif,image/jpeg,image/png,image/webp,image/gif',
        }),
        help_text='Envie somente fotos nos formatos JPG, JPEG, PNG, WEBP, GIF ou JFIF.',
    )
