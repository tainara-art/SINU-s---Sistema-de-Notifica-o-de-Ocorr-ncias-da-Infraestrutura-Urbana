from rest_framework import serializers

from .models import Ocorrencia, HistoricoStatus
from Fotos.models import Fotos
from Fotos.validators import MAX_FOTOS_POR_OCORRENCIA, validate_image_file


class FotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fotos
        fields = ['id', 'arquivo', 'date_send']


class HistoricoStatusSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoStatus
        fields = ['id', 'status_anterior', 'status_novo', 'observacao',
                  'responsavel', 'responsavel_nome', 'alterado_em']
        read_only_fields = ['id', 'alterado_em']

    def get_responsavel_nome(self, obj):
        return obj.responsavel.name if obj.responsavel else None


class OcorrenciaSerializer(serializers.ModelSerializer):
    fotos_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text='Envie até 5 fotos nos formatos JPG, JPEG, PNG, WEBP, GIF ou JFIF.',
    )
    fotos      = FotosSerializer(source='fotos_da_ocorrencia', many=True, read_only=True)
    historico  = HistoricoStatusSerializer(many=True, read_only=True)

    class Meta:
        model = Ocorrencia
        fields = ["id", "descricao", "cep", "latitude", "longitude",
                  "status", "prioridade", "categoria", "anonima",
                  "usuario", "prefeitura", "secretaria",
                  "date_created", "date_update",
                  "fotos", "fotos_upload", "historico"]
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
        for imagem in fotos_data:
            Fotos.objects.create(ocorrencia=ocorrencia, arquivo=imagem)
        return ocorrencia

    def update(self, instance, validated_data):
        fotos_data = validated_data.pop('fotos_upload', [])
        if fotos_data:
            total = instance.fotos_da_ocorrencia.count() + len(fotos_data)
            if total > MAX_FOTOS_POR_OCORRENCIA:
                raise serializers.ValidationError(
                    f'Adicionar essas fotos excederia o limite de {MAX_FOTOS_POR_OCORRENCIA}.'
                )

        instance = super().update(instance, validated_data)
        for imagem in fotos_data:
            Fotos.objects.create(ocorrencia=instance, arquivo=imagem)
        return instance
