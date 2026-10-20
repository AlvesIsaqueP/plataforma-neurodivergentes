from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Responsavel


class Aluno(models.Model):
    ESTILOS_APRENDIZAGEM = [
        ('jogos', 'Jogos'),
        ('video', 'Vídeo'),
        ('slide', 'Slide'),
        ('leitura', 'Leitura'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField(null=True, blank=True)
    responsavel = models.ForeignKey(Responsavel, on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos')
    preferencias = models.TextField(blank=True, help_text="Ex: prefere baixo estímulo")
    estilo_aprendizagem = models.CharField(max_length=20, choices=ESTILOS_APRENDIZAGEM, blank=True)

    def __str__(self):
        return self.nome