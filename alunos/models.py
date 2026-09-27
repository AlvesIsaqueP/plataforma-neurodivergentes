from django.db import models
from usuarios.models import Responsavel


class Aluno(models.Model):
    ESTILOS_APRENDIZAGEM = [
        ('jogos', 'Jogos'),
        ('video', 'Vídeo'),
        ('slide', 'Slide'),
        ('leitura', 'Leitura'),
    ]

    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    responsavel = models.ForeignKey(Responsavel, on_delete=models.CASCADE, related_name='alunos')
    preferencias = models.TextField(blank=True, help_text="Ex: prefere baixo estímulo")
    estilo_aprendizagem = models.CharField(max_length=20, choices=ESTILOS_APRENDIZAGEM, blank=True)

    def __str__(self):
        return self.nome