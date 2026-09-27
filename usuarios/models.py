from django.db import models
from django.contrib.auth.models import User


class Professor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150)
    especialidade = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.nome


class Responsavel(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True)
    data_consentimento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nome