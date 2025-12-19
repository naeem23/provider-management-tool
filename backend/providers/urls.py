from rest_framework.routers import DefaultRouter
from .views import ProviderViewSet

router = DefaultRouter()
router.register(r"providers", ProviderViewSet, basename="providers")

urlpatterns = router.urls
