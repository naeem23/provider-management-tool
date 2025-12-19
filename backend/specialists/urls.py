from rest_framework.routers import DefaultRouter
from .views import SpecialistViewSet

router = DefaultRouter()
router.register(r"specialists", SpecialistViewSet, basename="specialists")

urlpatterns = router.urls
