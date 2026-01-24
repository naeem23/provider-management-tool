from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register(r"service-orders", ServiceOrderViewSet, basename="service-orders")
router.register(r"extensions", ServiceOrderExtensionViewSet, basename="extensions")
router.register(r"substitutions", ServiceOrderSubstitutionViewSet, basename="substitutions")

urlpatterns = router.urls


"""
This will generate the following URLs:

SERVICE ORDERS:
GET    /api/orders/service-orders/                    - List all service orders
POST   /api/orders/service-orders/                    - Create service order
GET    /api/orders/service-orders/{id}/               - Get service order detail
PUT    /api/orders/service-orders/{id}/               - Update service order
PATCH  /api/orders/service-orders/{id}/               - Partial update
DELETE /api/orders/service-orders/{id}/               - Delete service order
GET    /api/orders/service-orders/{id}/extensions/    - Get extensions for order
GET    /api/orders/service-orders/{id}/substitutions/ - Get substitutions for order
POST   /api/orders/service-orders/{id}/complete/      - Complete service order

EXTENSIONS:
GET    /api/orders/extensions/                        - List all extensions
POST   /api/orders/extensions/                        - Create extension request
GET    /api/orders/extensions/{id}/                   - Get extension detail
POST   /api/orders/extensions/{id}/approve_extension/  - Supplier approves
POST   /api/orders/extensions/{id}/reject/            - Reject extension

SUBSTITUTIONS:
GET    /api/orders/substitutions/                     - List all substitutions
POST   /api/orders/substitutions/                     - Create substitution request
GET    /api/orders/substitutions/{id}/                - Get substitution detail
POST   /api/orders/substitutions/{id}/approve_substitution/  - Supplier approves
POST   /api/orders/substitutions/{id}/reject/            - Reject substitution
"""