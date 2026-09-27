from django.contrib import admin
from .models import Materia, Atividade, Questao, Progresso

admin.site.register(Materia)
admin.site.register(Atividade)
admin.site.register(Questao)
admin.site.register(Progresso)