from rest_framework import serializers
from .models import Materia, Atividade, Questao, Progresso


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = '__all__'


class AtividadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atividade
        fields = '__all__'


class QuestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questao
        fields = '__all__'


class ProgressoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progresso
        fields = '__all__'