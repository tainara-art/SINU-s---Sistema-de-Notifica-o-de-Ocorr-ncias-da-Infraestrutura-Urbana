from rest_framework import generics
from Prefeitura.models import Prefeitura
from Prefeitura.serializers import PrefeituraSerializer

class PrefeituraListCreate(generics.ListCreateAPIView):
    queryset = Prefeitura.objects.all()
    serializer_class = PrefeituraSerializer

class PrefeituraRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):    
    queryset = Prefeitura.objects.all()
    serializer_class = PrefeituraSerializer