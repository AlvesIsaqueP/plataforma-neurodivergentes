from django import forms
from alunos.models import Aluno
from .models import Materia, Aula, Atividade, Questao


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nome']


class _AlunosMixin:
    """Lista de alunos (só os que têm login) com caixas de seleção."""

    def _configurar_alunos(self):
        campo = self.fields['alunos']
        campo.widget = forms.CheckboxSelectMultiple()
        campo.queryset = Aluno.objects.filter(usuario__isnull=False).order_by('nome')
        campo.required = False


class AulaForm(_AlunosMixin, forms.ModelForm):
    class Meta:
        model = Aula
        fields = ['materia', 'titulo', 'descricao', 'link', 'alunos']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 5})}
        labels = {'alunos': 'Quem vai receber esta aula'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configurar_alunos()


class AtribuirAulaForm(_AlunosMixin, forms.ModelForm):
    class Meta:
        model = Aula
        fields = ['alunos']
        labels = {'alunos': 'Quem vai receber esta aula'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configurar_alunos()


class AtribuirAtividadeForm(_AlunosMixin, forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['alunos']
        labels = {'alunos': 'Quem vai receber esta atividade'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configurar_alunos()


class SlidesForm(forms.Form):
    pdf = forms.FileField(label='Arquivo PDF dos slides')

    def clean_pdf(self):
        arquivo = self.cleaned_data['pdf']
        if not arquivo.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Envie um arquivo PDF. No PowerPoint: Arquivo > Exportar > PDF.')
        return arquivo


class VideoForm(forms.Form):
    youtube = forms.CharField(label='Link do YouTube', required=False)
    arquivo = forms.FileField(label='ou arquivo de vídeo (MP4 ou WebM, até 50 MB)', required=False)

    def clean(self):
        dados = super().clean()
        link, arquivo = (dados.get('youtube') or '').strip(), dados.get('arquivo')
        if bool(link) == bool(arquivo):
            raise forms.ValidationError('Informe um link do YouTube ou escolha um arquivo, só um dos dois.')
        if link:
            from .videos import extrair_youtube_id
            dados['youtube_id'] = extrair_youtube_id(link)
            if not dados['youtube_id']:
                self.add_error('youtube', 'Esse não parece um link válido do YouTube.')
        return dados


class AtividadeForm(_AlunosMixin, forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo', 'materia', 'tipo', 'descricao', 'nivel_dificuldade', 'arquivo_ou_url', 'alunos']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 4})}
        labels = {'alunos': 'Quem vai receber esta atividade'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configurar_alunos()


class QuestaoForm(forms.ModelForm):
    LETRAS = 'ABCDE'
    CORRETAS = [('', '---------')] + [(l, f'Alternativa {l}') for l in LETRAS]
    GAB = [('', '---------'), ('V', 'Verdadeiro'), ('F', 'Falso')]

    alt_a = forms.CharField(label='Alternativa A', required=False)
    gab_a = forms.ChoiceField(label='A alternativa A é', required=False, choices=GAB)
    alt_b = forms.CharField(label='Alternativa B', required=False)
    gab_b = forms.ChoiceField(label='A alternativa B é', required=False, choices=GAB)
    alt_c = forms.CharField(label='Alternativa C', required=False)
    gab_c = forms.ChoiceField(label='A alternativa C é', required=False, choices=GAB)
    alt_d = forms.CharField(label='Alternativa D', required=False)
    gab_d = forms.ChoiceField(label='A alternativa D é', required=False, choices=GAB)
    alt_e = forms.CharField(label='Alternativa E', required=False)
    gab_e = forms.ChoiceField(label='A alternativa E é', required=False, choices=GAB)
    correta = forms.ChoiceField(
        label='Resposta correta', required=False, choices=CORRETAS,
        help_text='Qual alternativa está certa.')

    class Meta:
        model = Questao
        fields = ['enunciado', 'tipo_resposta', 'peso']
        widgets = {
            'enunciado': forms.Textarea(attrs={'rows': 3}),
            'peso': forms.NumberInput(attrs={'step': '0.5', 'min': '0.5'}),
        }
        labels = {'peso': 'Valor da questão (pontos)', 'tipo_resposta': 'Tipo de questão'}
        help_texts = {'peso': 'A nota final de 0 a 10 considera o valor de cada questão.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo = self.fields['tipo_resposta']
        campo.choices = Questao.TIPOS_RESPOSTA
        campo.initial = 'multipla_escolha'
        q = self.instance
        if q.pk and not self.is_bound:
            if q.tipo_resposta == 'multipla_escolha':
                for i, texto in enumerate(q.opcoes or []):
                    if i < len(self.LETRAS):
                        self.fields[f'alt_{self.LETRAS[i].lower()}'].initial = texto
                self.fields['correta'].initial = q.letra_correta
            for letra, texto, gab in q.afirmativas:
                self.fields[f'alt_{letra.lower()}'].initial = texto
                self.fields[f'gab_{letra.lower()}'].initial = gab

    def clean(self):
        dados = super().clean()
        tipo = dados.get('tipo_resposta')
        correta = dados.get('correta') or ''
        dados['opcoes_lista'], dados['texto_correto'] = [], ''
        if (self.instance.pk and tipo and tipo != self.instance.tipo_resposta
                and self.instance.respostas.exists()):
            self.add_error('tipo_resposta', 'Esta questão já tem respostas de alunos, então o tipo não pode mudar.')
            return dados
        if tipo == 'multipla_escolha':
            textos = {l: (dados.get(f'alt_{l.lower()}') or '').strip() for l in self.LETRAS}
            preenchidas = [l for l in self.LETRAS if textos[l]]
            if len(preenchidas) < 2:
                self.add_error('alt_b', 'Preencha pelo menos duas alternativas.')
            elif preenchidas != list(self.LETRAS[:len(preenchidas)]):
                self.add_error('alt_a', 'Preencha as alternativas em ordem, sem pular letras (A, B, C...).')
            elif correta not in preenchidas:
                self.add_error('correta', 'Escolha uma das alternativas preenchidas como correta.')
            else:
                dados['opcoes_lista'] = [textos[l] for l in preenchidas]
                dados['texto_correto'] = textos[correta]
        elif tipo == 'verdadeiro_falso':
            textos = {l: (dados.get(f'alt_{l.lower()}') or '').strip() for l in self.LETRAS}
            preenchidas = [l for l in self.LETRAS if textos[l]]
            if not preenchidas:
                self.add_error('alt_a', 'Escreva pelo menos uma afirmação.')
            elif preenchidas != list(self.LETRAS[:len(preenchidas)]):
                self.add_error('alt_a', 'Preencha as alternativas em ordem, sem pular letras (A, B, C...).')
            else:
                gabs = [dados.get(f'gab_{l.lower()}') or '' for l in preenchidas]
                faltam = False
                for l, g in zip(preenchidas, gabs):
                    if not g:
                        self.add_error(f'gab_{l.lower()}', 'Marque Verdadeiro ou Falso.')
                        faltam = True
                if not faltam:
                    dados['opcoes_lista'] = [textos[l] for l in preenchidas]
                    dados['texto_correto'] = ','.join(gabs)
        return dados

    def save(self, commit=True):
        q = super().save(commit=False)
        q.opcoes = self.cleaned_data['opcoes_lista'] or None
        q.resposta_correta = self.cleaned_data['texto_correto']
        if commit:
            q.save()
        return q


class CorrecaoForm(forms.Form):
    """Uma nota por questão aberta (de 0 até o valor da questão) e um comentário geral."""

    comentario = forms.CharField(label='Comentário para o aluno', required=False,
                                 widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, abertas, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.abertas = list(abertas)
        for r in self.abertas:
            self.fields[f'nota_{r.pk}'] = forms.DecimalField(
                label=f'Nota da questão (0 a {r.questao.peso:g})', min_value=0,
                max_value=r.questao.peso, decimal_places=1,
                initial=r.pontos,
                widget=forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': f'{r.questao.peso:g}'}))
        self.order_fields([f'nota_{r.pk}' for r in self.abertas] + ['comentario'])
