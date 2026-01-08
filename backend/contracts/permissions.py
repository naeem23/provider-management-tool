from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsContractCoordinator(BasePermission):
    """
    Contract Coordinator.
    """
    def has_permission(self, request, view):
        # Skip role check for Flowable requests
        if getattr(request, 'is_flowable', False):
            return True

        return request.user.role == UserRole.CONTRACT_COORDINATOR


class CanApproveContract(BasePermission):
    """
    Only Provider Admin can activate contracts.
    """
    def has_permission(self, request, view):
        return request.user.role == UserRole.CONTRACT_COORDINATOR
