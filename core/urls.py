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
    path('materias/<int:pk>/aulas/nova/', paginas.aula_nova, name='aula_nova'),
    path('atividades/', paginas.atividades, name='atividades'),
    path('atividades/nova/', paginas.atividade_nova, name='atividade_nova'),
    path('atividades/<int:pk>/', paginas.atividade_detalhe, name='atividade'),
    path('atividades/<int:pk>/questoes/nova/', paginas.questao_nova, name='questao_nova'),
    path('atividades/<int:pk>/responder/', paginas.responder, name='responder'),
    path('notas/', paginas.notas, name='notas'),
    path('alunos/', paginas.alunos, name='alunos'),
    path('alunos/<int:pk>/', paginas.aluno_detalhe, name='aluno'),
    path('correcoes/<int:pk>/', paginas.corrigir, name='corrigir'),
]
