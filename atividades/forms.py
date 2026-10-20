from django import forms
from .models import Materia, Aula, Atividade, Questao


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nome']


class AulaForm(forms.ModelForm):
    class Meta:
        model = Aula
        fields = ['titulo', 'descricao', 'link']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 5})}


class SlidesForm(forms.Form):
    pdf = forms.FileField(label='Arquivo PDF dos slides')

    def clean_pdf(self):
        arquivo = self.cleaned_data['pdf']
        if not arquivo.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Envie um arquivo PDF. No PowerPoint: Arquivo > Exportar > PDF.')
        return arquivo


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['titulo', 'materia', 'tipo', 'descricao', 'nivel_dificuldade', 'arquivo_ou_url']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 4})}


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
