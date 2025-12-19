from rest_framework.permissions import BasePermission


class IsProviderAdmin(BasePermission):
    """
    Allow access to provider admins only.
    """
    def has_permission(self, request, view):
        return request.user.role == "PROVIDER_ADMIN"


# Optional For Now
class IsSameProviderOrStaff(BasePermission):
    """
    Only allow users to manage specialists within their provider.
    Staff users can see and edit specialists for all providers.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.provider == obj.provider
