from rest_framework.permissions import BasePermission
from accounts.models import UserRole
from .models import RequestStatus, OfferStatus


class CanManageServiceRequest(BasePermission):
    """
    Provider Admin / Internal PM can create and manage requests.
    """
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.PROVIDER_ADMIN,
            UserRole.INTERNAL_PM,
        ]


class CanEditServiceRequest(BasePermission):
    """
    Requests can only be edited before they are OPEN.
    """
    def has_object_permission(self, request, view, obj):
        return obj.status == RequestStatus.IMPORTED


class IsSupplierRep(BasePermission):
    def has_permission(self, request, view):
        # Skip role check for Flowable requests
        if getattr(request, 'is_flowable', False):
            return True

        return request.user.role == UserRole.SUPPLIER_REP


class CanEditDraftOffer(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Skip role check for Flowable requests
        if getattr(request, 'is_flowable', False):
            return True
            
        return (
            obj.status == OfferStatus.DRAFT
            and obj.provider_id == request.user.provider_id
        )


class CanViewOffer(BasePermission):
    """
    Supplier sees own offers.
    Admin / Internal PM sees all.
    """
    def has_object_permission(self, request, view, obj):
        # Skip role check for Flowable requests
        if getattr(request, 'is_flowable', False):
            return True

        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj.provider_id == request.user.provider_id


class CanDecideOffer(BasePermission):
    """
    Only Internal PM (or staff) can accept/reject offers.
    """
    def has_permission(self, request, view):
        # Skip role check for Flowable requests
        if getattr(request, 'is_flowable', False):
            return True
            
        return (
            request.user.is_staff
            or request.user.role == UserRole.INTERNAL_PM
        )


class IsAuthenticatedOrFlowable(BasePermission):
    """
    Allow access if user is authenticated OR request is from Flowable
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.user.is_superuser or getattr(request, 'is_flowable', False)
