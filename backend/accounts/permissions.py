from rest_framework.permissions import BasePermission
from .models import UserRole


class IsProviderAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and request.user.role == UserRole.PROVIDER_ADMIN
        )


class IsProviderAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Provider Admin can do anything
        if request.user.role == UserRole.PROVIDER_ADMIN:
            return True

        # Otherwise, user can act only on own object
        return bool(obj == request.user)


class IsSameProviderOrStaff(BasePermission):
    """
    Provider isolation: user can access users within same provider.
    Admin/staff can access all.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return getattr(request.user, "provider_id", None) is not None and request.user.provider_id == obj.provider_id
