from django.db import models
from usuarios.models import Professor
from alunos.models import Aluno


class Materia(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Atividade(models.Model):
    TIPOS = [
        ('jogo', 'Jogo'),
        ('questionario', 'Questionário'),
        ('video', 'Vídeo'),
        ('slide', 'Slide'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='atividades')
    descricao = models.TextField(blank=True)
    nivel_dificuldade = models.PositiveSmallIntegerField(default=1)
    arquivo_ou_url = models.CharField(max_length=500, blank=True)
    criado_por = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, related_name='atividades')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Questao(models.Model):
    TIPOS_RESPOSTA = [
        ('multipla_escolha', 'Múltipla escolha'),
        ('verdadeiro_falso', 'Verdadeiro/Falso'),
        ('aberta', 'Aberta'),
    ]

    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='questoes')
    enunciado = models.TextField()
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)
    opcoes = models.JSONField(blank=True, null=True)
    resposta_correta = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"Questão de {self.atividade.titulo}"


class Progresso(models.Model):
    STATUS = [
        ('nao_iniciado', 'Não iniciado'),
        ('em_andamento', 'Em andamento'),
        ('concluido', 'Concluído'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='progressos')
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='progressos')
    status = models.CharField(max_length=20, choices=STATUS, default='nao_iniciado')
    pontuacao = models.FloatField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('aluno', 'atividade')

    def __str__(self):
        return f"{self.aluno.nome} - {self.atividade.titulo}"