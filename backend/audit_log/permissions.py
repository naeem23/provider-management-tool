from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class CanViewAuditLogs(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.PROVIDER_ADMIN,
            UserRole.CONTRACT_COORDINATOR,
            UserRole.INTERNAL_PM,
        ]
