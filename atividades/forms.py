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
    opcoes_texto = forms.CharField(
        label='Opções (uma por linha)', required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Só para múltipla escolha.',
    )

    class Meta:
        model = Questao
        fields = ['enunciado', 'tipo_resposta', 'resposta_correta']
        widgets = {'enunciado': forms.Textarea(attrs={'rows': 3})}
        help_texts = {
            'resposta_correta': 'Múltipla escolha: copie exatamente uma das opções. '
                                'Verdadeiro/Falso: escreva Verdadeiro ou Falso. Aberta: deixe em branco.',
        }

    def clean(self):
        dados = super().clean()
        tipo = dados.get('tipo_resposta')
        correta = (dados.get('resposta_correta') or '').strip()
        opcoes = [l.strip() for l in (dados.get('opcoes_texto') or '').splitlines() if l.strip()]
        if tipo == 'multipla_escolha':
            if len(opcoes) < 2:
                self.add_error('opcoes_texto', 'Informe pelo menos 2 opções.')
            elif correta not in opcoes:
                self.add_error('resposta_correta', 'A resposta correta precisa ser igual a uma das opções.')
        elif tipo == 'verdadeiro_falso':
            opcoes = ['Verdadeiro', 'Falso']
            if correta not in opcoes:
                self.add_error('resposta_correta', 'Escreva Verdadeiro ou Falso.')
        elif tipo == 'aberta':
            opcoes, correta = [], ''
        dados['opcoes_lista'] = opcoes
        dados['resposta_correta'] = correta
        return dados

    def save(self, commit=True):
        q = super().save(commit=False)
        q.opcoes = self.cleaned_data['opcoes_lista'] or None
        q.resposta_correta = self.cleaned_data['resposta_correta']
        if commit:
            q.save()
        return q


class CorrecaoForm(forms.Form):
    nota = forms.DecimalField(label='Nota (0 a 10)', min_value=0, max_value=10, decimal_places=1)
    comentario = forms.CharField(label='Comentário para o aluno', required=False,
                                 widget=forms.Textarea(attrs={'rows': 3}))
