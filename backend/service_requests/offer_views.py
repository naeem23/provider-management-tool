from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from service_orders.models import ServiceOrder
from .models import ServiceOffer, OfferStatus, RequestStatus
from .offer_serializers import (
    ServiceOfferReadSerializer,
    ServiceOfferCreateSerializer,
)
from .permissions import (
    IsSupplierRep,
    CanEditDraftOffer,
    CanViewOffer,
    CanDecideOffer,
)
from audit_log.models import AuditLog
from specialists.models import Specialist
from accounts.models import User, UserRole
from notifications.services import notify_roles


class ServiceOfferViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ServiceOffer.objects.select_related(
        "request", "provider", "proposed_specialist"
    )
    permission_classes = [IsAuthenticated,]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser or getattr(self.request, "is_flowable", False):
            return self.queryset.order_by("-created_at")

        # Supplier sees only own provider offers
        if user.provider_id:
            return self.queryset.filter(provider_id=user.provider_id).order_by("-created_at")

        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == ["create", "update", "partial_update"]:
            return ServiceOfferCreateSerializer
        return ServiceOfferReadSerializer

    def get_permissions(self):
        if self.action == "update_status":
            return [AllowAny(),]
        if self.action in ["create", "metrics"]:
            return [IsAuthenticated(), IsSupplierRep()]
        if self.action in ["update", "partial_update", "withdraw"]:
            return [IsAuthenticated(), IsSupplierRep(), CanEditDraftOffer()]
        return super().get_permissions()


    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """
        Withdraw a submitted offer.
        """
        offer = self.get_object()

        if offer.status not in [OfferStatus.DRAFT, OfferStatus.SUBMITTED, OfferStatus.UNDER_REVIEW]:
            return Response(
                {"detail": "Only draft/submitted/under review offers can be withdrawn."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offer.status = OfferStatus.WITHDRAWN
        offer.save(update_fields=["status"])
        
        # AUDIT LOG
        AuditLog.log_action(
            user=request.user,
            action_type='OFFER_WITHDRAWN',
            action_category='OFFER_MANAGEMENT',
            description=f'Offer withdrawn for ID {str(service_request.id)}',
            entity_type='ServiceOffer',
            entity_id=offer.id,
            metadata={
                'offer_id': str(offer.id),
                'status': offer.status,
                'specialist': offer.proposed_specialist.full_name,
                'daily_rate': str(offer.daily_rate),
            },
            request=request
        )

        # Notification withdrawn 
        notify_roles(
            role="SUPPLIER_REP",
            title="Offer status updated",
            message=f"Offer status changed to {offer.status}.",
            entity_type="ServiceOffer",
            entity_id=offer.id,
        )

        return Response({"status": "WITHDRAWN"})


    @action(detail=False, methods=["post"], url_path="update-status")
    def update_status(self, request):
        offer_id = request.data.get("id")
        offer_status = request.data.get("status")

        if not offer_id or not offer_status:
            return Response(
                {"detail": "offer id and status are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if offer_status not in ["UNDER_REVIEW", "ACCEPTED", "REJECTED"]:
            return Response(
                {"detail": "Valid status are ACCEPTED/REJECTED."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch offer
        offer = get_object_or_404(ServiceOffer, id=offer_id)

        if offer.status != OfferStatus.SUBMITTED:
            return Response(
                {"detail": "Only submitted offers can be accepted/rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offer.status = offer_status
        offer.save(update_fields=["status"])

        # Notification
        notify_roles(
            role="SUPPLIER_REP",
            title="Offer Status Updated",
            message=f"Offer status changed to {offer.status}.",
            entity_type="ServiceOffer",
            entity_id=offer.id,
        )
        
        return Response(
            {
                "message": "Offer status updated successfully.",
                "offer_id": str(offer.id),
                "status": offer.status,
            },
            status=status.HTTP_200_OK,
        )


    @action(detail=False, methods=['get'], url_path='metrics')
    def metrics(self, request):
        """
        Get dashboard metrics for supplier representative.
        Returns counts of offers by status and available specialists.
        """
        user = request.user
        
        # Get offer counts by status
        offer_counts = self.get_queryset().aggregate(
            accepted_offers=Count('id', filter=Q(status='ACCEPTED')),
            pending_offers=Count('id', filter=Q(status='SUBMITTED')),
            rejected_offers=Count('id', filter=Q(status='REJECTED'))
        )
        
        # Get available specialists count
        available_specialists = Specialist.objects.filter(
            provider=request.user.provider,
            status='Active'
        ).count()
        
        metrics_data = {
            "accepted_offers": offer_counts.get('accepted_offers', 0),
            "pending_offers": offer_counts.get('pending_offers', 0),
            "rejected_offers": offer_counts.get('rejected_offers', 0),
            "available_specialists": available_specialists
        }
        
        return Response(metrics_data, status=status.HTTP_200_OK)