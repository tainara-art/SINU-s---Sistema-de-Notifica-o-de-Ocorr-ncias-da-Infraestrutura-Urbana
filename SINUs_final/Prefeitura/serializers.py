from rest_framework import serializers
from .models import Prefeitura

class PrefeituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prefeitura
        fields = '__all__'
