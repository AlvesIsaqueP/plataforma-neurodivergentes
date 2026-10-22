from django.core.validators import MinValueValidator
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
    peso = models.FloatField(default=1, validators=[MinValueValidator(0.1)], help_text="Pontos que a questão vale")

    LETRAS = 'ABCDEFGHIJ'

    @property
    def alternativas(self):
        """Lista de (letra, texto). Verdadeiro/Falso não usa letras."""
        opcoes = self.opcoes or []
        if self.tipo_resposta == 'multipla_escolha':
            return [(self.LETRAS[i], t) for i, t in enumerate(opcoes[:len(self.LETRAS)])]
        return [('', t) for t in opcoes]

    @property
    def letra_correta(self):
        for letra, texto in self.alternativas:
            if texto == self.resposta_correta:
                return letra
        return ''

    @property
    def afirmativas(self):
        """Verdadeiro/Falso em lista: [(letra, texto, 'V' ou 'F')]. Vazio nas demais (e no V/F antigo, de uma só afirmação)."""
        if self.tipo_resposta != 'verdadeiro_falso' or self.resposta_correta in ('', 'Verdadeiro', 'Falso'):
            return []
        gab = self.resposta_correta.split(',')
        return [(self.LETRAS[i], t, gab[i] if i < len(gab) else '')
                for i, t in enumerate((self.opcoes or [])[:len(self.LETRAS)])]

    def pontuar(self, texto):
        """Correção automática: devolve (correta, pontos). Em V/F por itens, a nota é proporcional aos acertos."""
        itens = self.afirmativas
        if itens:
            marcadas = texto.split(',')
            acertos = sum(1 for i, (_, _, g) in enumerate(itens) if i < len(marcadas) and marcadas[i] == g)
            return acertos == len(itens), round(self.peso * acertos / len(itens), 2)
        correta = texto == self.resposta_correta
        return correta, (self.peso if correta else 0)

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

    def calcular_nota(self):
        """Nota de 0 a 10 somando quiz e questões abertas; None se falta corrigir algo."""
        respostas = list(self.respostas.select_related('questao'))
        if not respostas:
            return None
        pontos = [r.pontos_efetivos for r in respostas]
        if any(p is None for p in pontos):
            return None
        total = sum(r.questao.peso for r in respostas)
        return round(10 * sum(pontos) / total, 1) if total else None

    def __str__(self):
        return f"{self.aluno.nome} - {self.atividade.titulo}"


class Resposta(models.Model):
    progresso = models.ForeignKey(Progresso, on_delete=models.CASCADE, related_name='respostas')
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE, related_name='respostas')
    texto = models.TextField()
    correta = models.BooleanField(null=True, blank=True)
    pontos = models.FloatField(null=True, blank=True)

    @property
    def itens(self):
        """V/F por itens: [(letra, texto, marcada, certa, acertou)]."""
        marcadas = self.texto.split(',')
        nomes = {'V': 'Verdadeiro', 'F': 'Falso'}
        return [(l, t, nomes.get(marcadas[i] if i < len(marcadas) else '', '—'), nomes.get(g, g),
                 i < len(marcadas) and marcadas[i] == g)
                for i, (l, t, g) in enumerate(self.questao.afirmativas)]

    @property
    def pontos_efetivos(self):
        """Pontos ganhos; None enquanto uma questão aberta não foi corrigida."""
        if self.pontos is not None:
            return self.pontos
        if self.correta is True:
            return self.questao.peso
        if self.correta is False:
            return 0
        return None

    class Meta:
        unique_together = ('progresso', 'questao')

    def __str__(self):
        return f"Resposta de {self.progresso.aluno.nome}"
