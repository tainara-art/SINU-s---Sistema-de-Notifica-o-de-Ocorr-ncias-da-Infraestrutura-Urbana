from rest_framework import generics
from .models import Secretaria
from .serializers import SecretariaSerializer

class SecretariaListCreate(generics.ListCreateAPIView):
    queryset = Secretaria.objects.all()
    serializer_class = SecretariaSerializer

class SecretariaRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Secretaria.objects.all()
    serializer_class = SecretariaSerializer