from django.contrib.auth import login
from django.shortcuts import render, redirect
from rest_framework import viewsets

from .forms import CadastroForm
from .models import Professor, Responsavel
from .permissions import SomenteProfessor
from .serializers import ProfessorSerializer, ResponsavelSerializer


class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [SomenteProfessor]


class ResponsavelViewSet(viewsets.ModelViewSet):
    queryset = Responsavel.objects.all()
    serializer_class = ResponsavelSerializer
    permission_classes = [SomenteProfessor]


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('home')
    else:
        form = CadastroForm()
    return render(request, 'usuarios/cadastro.html', {'form': form})
