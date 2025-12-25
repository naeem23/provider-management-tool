from rest_framework.permissions import BasePermission
from accounts.models import UserRole
from .models import OrderStatus


class CanViewOrder(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.provider_id == request.user.provider_id


class CanManageOrder(BasePermission):
    """
    Internal PM manages order lifecycle.
    """
    def has_permission(self, request, view):
        return request.user.role == UserRole.INTERNAL_PM


class CanRequestSubstitution(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == UserRole.SUPPLIER_REP


class CanRequestExtension(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == UserRole.INTERNAL_PM
