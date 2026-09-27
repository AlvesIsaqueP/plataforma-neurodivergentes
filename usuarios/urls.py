from rest_framework.routers import DefaultRouter
from .views import ProfessorViewSet, ResponsavelViewSet

router = DefaultRouter()
router.register(r'professores', ProfessorViewSet)
router.register(r'responsaveis', ResponsavelViewSet)

urlpatterns = router.urls