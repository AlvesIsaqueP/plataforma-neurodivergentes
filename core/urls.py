"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from atividades import views_web as paginas
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('alunos.urls')),
    path('api/', include('usuarios.urls')),
    path('api/', include('atividades.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('cadastro/', usuarios_views.cadastro, name='cadastro'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('', paginas.home, name='home'),
    path('materias/', paginas.materias, name='materias'),
    path('materias/nova/', paginas.materia_nova, name='materia_nova'),
    path('materias/<int:pk>/', paginas.materia_detalhe, name='materia'),
    path('materias/<int:pk>/excluir/', paginas.materia_excluir, name='materia_excluir'),
    path('aulas/', paginas.aulas, name='aulas'),
    path('aulas/nova/', paginas.aula_nova, name='aula_nova'),
    path('aulas/<int:pk>/', paginas.aula_detalhe, name='aula'),
    path('aulas/<int:pk>/video/', paginas.aula_video, name='aula_video'),
    path('aulas/<int:pk>/video/remover/', paginas.aula_video_remover, name='aula_video_remover'),
    path('aulas/<int:pk>/excluir/', paginas.aula_excluir, name='aula_excluir'),
    path('aulas/<int:pk>/atribuir/', paginas.aula_atribuir, name='aula_atribuir'),
    path('aulas/<int:pk>/slides/', paginas.aula_slides, name='aula_slides'),
    path('aulas/<int:pk>/slides/remover/', paginas.aula_slides_remover, name='aula_slides_remover'),
    path('atividades/', paginas.atividades, name='atividades'),
    path('atividades/nova/', paginas.atividade_nova, name='atividade_nova'),
    path('atividades/<int:pk>/', paginas.atividade_detalhe, name='atividade'),
    path('atividades/<int:pk>/excluir/', paginas.atividade_excluir, name='atividade_excluir'),
    path('questoes/<int:pk>/editar/', paginas.questao_editar, name='questao_editar'),
    path('questoes/<int:pk>/excluir/', paginas.questao_excluir, name='questao_excluir'),
    path('atividades/<int:pk>/atribuir/', paginas.atividade_atribuir, name='atividade_atribuir'),
    path('atividades/<int:pk>/questoes/nova/', paginas.questao_nova, name='questao_nova'),
    path('atividades/<int:pk>/responder/', paginas.responder, name='responder'),
    path('notas/', paginas.notas, name='notas'),
    path('alunos/', paginas.alunos, name='alunos'),
    path('alunos/<int:pk>/', paginas.aluno_detalhe, name='aluno'),
    path('correcoes/<int:pk>/', paginas.corrigir, name='corrigir'),
]
