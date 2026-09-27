from rest_framework.routers import DefaultRouter
from .views import MateriaViewSet, AtividadeViewSet, QuestaoViewSet, ProgressoViewSet

router = DefaultRouter()
router.register(r'materias', MateriaViewSet)
router.register(r'atividades', AtividadeViewSet)
router.register(r'questoes', QuestaoViewSet)
router.register(r'progressos', ProgressoViewSet)

urlpatterns = router.urls