from rest_framework import viewsets
from usuarios.permissions import ProfessorEscreveTodosLeem, SomenteProfessor, eh_professor
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
    permission_classes = [SomenteProfessor]


class ProgressoViewSet(viewsets.ModelViewSet):
    queryset = Progresso.objects.all()
    serializer_class = ProgressoSerializer
    permission_classes = [ProfessorEscreveTodosLeem]

    def get_queryset(self):
        qs = Progresso.objects.all()
        if eh_professor(self.request.user):
            return qs
        return qs.filter(aluno__usuario=self.request.user)
