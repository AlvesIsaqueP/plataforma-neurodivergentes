from rest_framework import viewsets
from .models import Professor, Responsavel
from .serializers import ProfessorSerializer, ResponsavelSerializer


class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer


class ResponsavelViewSet(viewsets.ModelViewSet):
    queryset = Responsavel.objects.all()
    serializer_class = ResponsavelSerializer
# Create your views here.
