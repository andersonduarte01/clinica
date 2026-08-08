from rest_framework.routers import DefaultRouter

from apps.core.views.paciente import PacienteViewSet

router = DefaultRouter()
router.register(r"pacientes", PacienteViewSet, basename="paciente")

urlpatterns = router.urls
