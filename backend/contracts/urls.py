from rest_framework_nested.routers import NestedDefaultRouter
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, ContractVersionViewSet, PricingRuleViewSet

router = DefaultRouter()
router.register(r"contracts", ContractViewSet, basename="contracts")

contracts_router = NestedDefaultRouter(router, r"contracts", lookup="contract")
contracts_router.register(r"versions", ContractVersionViewSet, basename="contract-versions")
contracts_router.register(r"pricing-rules", PricingRuleViewSet, basename="pricing-rules")

urlpatterns = router.urls + contracts_router.urls
