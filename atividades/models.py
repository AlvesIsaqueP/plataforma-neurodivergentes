from django.db import models
from usuarios.models import Professor
from alunos.models import Aluno


class Materia(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Aula(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='aulas')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True, help_text="Link de vídeo, slide ou material (opcional)")
    criado_por = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True, related_name='aulas')
    alunos = models.ManyToManyField(Aluno, blank=True, related_name='aulas_atribuidas')
    youtube_id = models.CharField(max_length=11, blank=True)
    video_caminho = models.CharField(max_length=300, blank=True)

    @property
    def tem_video(self):
        return bool(self.youtube_id or self.video_caminho)

    @property
    def video_url(self):
        from .slides import url_publica
        return url_publica(self.video_caminho) if self.video_caminho else ''
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return self.titulo


class SlideAula(models.Model):
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='slides')
    numero = models.PositiveSmallIntegerField()
    caminho = models.CharField(max_length=300)
    texto = models.TextField(blank=True)

    class Meta:
        ordering = ['numero']
        unique_together = ('aula', 'numero')

    @property
    def url(self):
        from .slides import url_publica
        return url_publica(self.caminho)

    def __str__(self):
        return f"{self.aula.titulo} - slide {self.numero}"


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
    alunos = models.ManyToManyField(Aluno, blank=True, related_name='atividades_atribuidas')
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
        ('aguardando_correcao', 'Aguardando correção'),
        ('concluido', 'Concluído'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='progressos')
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='progressos')
    status = models.CharField(max_length=25, choices=STATUS, default='nao_iniciado')
    pontuacao = models.FloatField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    comentario = models.TextField(blank=True)

    class Meta:
        unique_together = ('aluno', 'atividade')

    def __str__(self):
        return f"{self.aluno.nome} - {self.atividade.titulo}"


class Resposta(models.Model):
    progresso = models.ForeignKey(Progresso, on_delete=models.CASCADE, related_name='respostas')
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='respostas')
    texto = models.TextField()
    correta = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ('progresso', 'questao')

    def __str__(self):
        return f"Resposta de {self.progresso.aluno.nome}"
