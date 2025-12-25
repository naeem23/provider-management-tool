from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class CanManageContracts(BasePermission):
    """
    Contract Coordinator or Provider Admin.
    """
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.CONTRACT_COORDINATOR,
            UserRole.PROVIDER_ADMIN,
        ]


class CanApproveContract(BasePermission):
    """
    Only Provider Admin can activate contracts.
    """
    def has_permission(self, request, view):
        return request.user.role == UserRole.PROVIDER_ADMIN
