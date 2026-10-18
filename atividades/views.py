from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from .models import Materia, Atividade, Questao, Progresso
from .serializers import (
    MateriaSerializer, AtividadeSerializer, QuestaoSerializer, ProgressoSerializer
)


class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer


class AtividadeViewSet(viewsets.ModelViewSet):
    queryset = Atividade.objects.all()
    serializer_class = AtividadeSerializer


class QuestaoViewSet(viewsets.ModelViewSet):
    queryset = Questao.objects.all()
    serializer_class = QuestaoSerializer


class ProgressoViewSet(viewsets.ModelViewSet):
    queryset = Progresso.objects.all()
    serializer_class = ProgressoSerializer

@login_required
def home(request):
    materias = Materia.objects.all()
    return render(request, 'atividades/home.html', {'materias': materias})