from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from alunos.models import Aluno
from .models import Professor


class CadastroForm(UserCreationForm):
    TIPOS = [('aluno', 'Aluno'), ('professor', 'Professor')]

    nome = forms.CharField(label='Nome completo', max_length=150)
    tipo = forms.ChoiceField(label='Eu sou', choices=TIPOS, initial='aluno')
    codigo_professor = forms.CharField(
        label='Código de professor', required=False,
        help_text='Só para professores. Peça o código à equipe do projeto.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def clean(self):
        dados = super().clean()
        if dados.get('tipo') == 'professor':
            esperado = getattr(settings, 'CODIGO_PROFESSOR', '')
            if not esperado or dados.get('codigo_professor', '').strip() != esperado:
                self.add_error('codigo_professor', 'Código de professor incorreto.')
        return dados

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=True)
        nome = self.cleaned_data['nome']
        if self.cleaned_data['tipo'] == 'professor':
            Professor.objects.create(usuario=usuario, nome=nome)
        else:
            Aluno.objects.create(usuario=usuario, nome=nome)
        return usuario
