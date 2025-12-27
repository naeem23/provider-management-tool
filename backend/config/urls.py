from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps
    path("api/accounts/", include("accounts.urls")),
    path("api/providers/", include("providers.urls")),
    path("api/specialists/", include("specialists.urls")),
    path("api/requests/", include("service_requests.urls")),
    path("api/orders/", include("service_orders.urls")),
    path("api/contracts/", include("contracts.urls")),
    path("api/audit/", include("audit_log.urls")),
    path("api/notifications/", include("notifications.urls")),
]
