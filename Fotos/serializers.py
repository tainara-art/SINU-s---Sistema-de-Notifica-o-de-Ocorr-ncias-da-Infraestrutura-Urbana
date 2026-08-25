from rest_framework import serializers

from Ocorrencias.models import Ocorrencia
from Fotos.models import Fotos
from Fotos.validators import MAX_FOTOS_POR_OCORRENCIA, validate_image_file


class FotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fotos
        fields = ['id', 'ocorrencia', 'arquivo', 'date_send']
        read_only_fields = ['id', 'date_send']

    def validate_arquivo(self, arquivo):
        try:
            validate_image_file(arquivo)
        except Exception as exc:
            raise serializers.ValidationError(str(exc))
        return arquivo


class OcorrenciaComFotoSerializer(serializers.ModelSerializer):
    fotos_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text='Envie até 5 fotos nos formatos JPG, JPEG, PNG, WEBP, GIF ou JFIF.',
    )
    fotos = FotosSerializer(source='fotos_da_ocorrencia', many=True, read_only=True)

    class Meta:
        model = Ocorrencia
        fields = [
            'id', 'descricao', 'cep', 'latitude', 'longitude',
            'status', 'prioridade', 'categoria', 'anonima',
            'usuario', 'prefeitura', 'secretaria',
            'date_created', 'date_update', 'fotos', 'fotos_upload',
        ]
        read_only_fields = ['id', 'date_created', 'date_update']

    def validate_fotos_upload(self, arquivos):
        if len(arquivos) > MAX_FOTOS_POR_OCORRENCIA:
            raise serializers.ValidationError(
                f'Máximo de {MAX_FOTOS_POR_OCORRENCIA} fotos por ocorrência.'
            )

        for arquivo in arquivos:
            try:
                validate_image_file(arquivo)
            except Exception as exc:
                raise serializers.ValidationError(str(exc))

        return arquivos

    def create(self, validated_data):
        fotos_data = validated_data.pop('fotos_upload', [])
        ocorrencia = Ocorrencia.objects.create(**validated_data)
        for arquivo in fotos_data:
            Fotos.objects.create(ocorrencia=ocorrencia, arquivo=arquivo)
        return ocorrencia
