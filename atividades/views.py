from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from usuarios.permissions import ProfessorEscreveTodosLeem
from .models import Materia, Atividade, Questao, Progresso
from .serializers import (
    MateriaSerializer, AtividadeSerializer, QuestaoSerializer, ProgressoSerializer
)


class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [ProfessorEscreveTodosLeem]


class AtividadeViewSet(viewsets.ModelViewSet):
    queryset = Atividade.objects.all()
    serializer_class = AtividadeSerializer
    permission_classes = [ProfessorEscreveTodosLeem]


class QuestaoViewSet(viewsets.ModelViewSet):
    queryset = Questao.objects.all()
    serializer_class = QuestaoSerializer
    permission_classes = [ProfessorEscreveTodosLeem]


class ProgressoViewSet(viewsets.ModelViewSet):
    queryset = Progresso.objects.all()
    serializer_class = ProgressoSerializer
    permission_classes = [IsAuthenticated]

@login_required
def home(request):
    materias = Materia.objects.all()
    return render(request, 'atividades/home.html', {'materias': materias})

@login_required
def materia_detalhe(request, pk):
    materia = get_object_or_404(Materia, pk=pk)
    atividades = materia.atividades.all()
    return render(request, 'atividades/materia.html', {'materia': materia, 'atividades': atividades})