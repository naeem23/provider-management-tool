from rest_framework.routers import DefaultRouter
from .views import (
    ServiceOrderViewSet,
    SubstitutionRequestViewSet,
    ExtensionRequestViewSet,
)

router = DefaultRouter()
router.register(r"service-orders", ServiceOrderViewSet, basename="service-orders")
router.register(r"substitutions", SubstitutionRequestViewSet, basename="substitutions")
router.register(r"extensions", ExtensionRequestViewSet, basename="extensions")

urlpatterns = router.urls
