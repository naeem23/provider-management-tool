from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from service_orders.models import ServiceOrder
from .models import ServiceOffer, OfferStatus, RequestStatus
from .offer_serializers import (
    ServiceOfferReadSerializer,
    ServiceOfferCreateSerializer,
    ServiceOfferUpdateSerializer,
)
from .permissions import (
    IsSupplierRep,
    CanEditDraftOffer,
    CanViewOffer,
    CanDecideOffer,
)
from audit_log.utils import log_audit_event
from audit_log.models import AuditAction


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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return self.queryset

        # Supplier sees only own provider offers
        if user.provider_id:
            return self.queryset.filter(provider_id=user.provider_id)

        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ServiceOfferCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ServiceOfferUpdateSerializer
        return ServiceOfferReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsSupplierRep()]
        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsSupplierRep(), CanEditDraftOffer()]
        if self.action in ["accept", "reject"]:
            return [IsAuthenticated(), CanDecideOffer()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(
            provider=self.request.user.provider,
            submitted_by=self.request.user,
            status=OfferStatus.DRAFT,
        )


    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """
        Submit a draft offer.
        """
        offer = self.get_object()

        if offer.status != OfferStatus.DRAFT:
            return Response(
                {"detail": "Only draft offers can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offer.status = OfferStatus.SUBMITTED
        offer.save(update_fields=["status"])
        
        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, offer)

        return Response({"status": "SUBMITTED"})


    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """
        Withdraw a submitted offer.
        """
        offer = self.get_object()

        if offer.status not in [OfferStatus.DRAFT, OfferStatus.SUBMITTED]:
            return Response(
                {"detail": "Only draft or submitted offers can be withdrawn."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offer.status = OfferStatus.WITHDRAWN
        offer.save(update_fields=["status"])
        
        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, offer)

        return Response({"status": "WITHDRAWN"})


    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        offer = self.get_object()

        if offer.status != OfferStatus.SUBMITTED:
            return Response(
                {"detail": "Only submitted offers can be accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request = offer.request

        if service_request.status == RequestStatus.AWARDED:
            return Response(
                {"detail": "An offer has already been accepted for this request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Accept this offer
            offer.status = OfferStatus.ACCEPTED
            offer.save(update_fields=["status"])

            # Reject all other submitted offers
            ServiceOffer.objects.filter(
                request=service_request,
                status=OfferStatus.SUBMITTED,
            ).exclude(id=offer.id).update(status=OfferStatus.REJECTED)

            # Update service request
            service_request.status = RequestStatus.AWARDED
            service_request.save(update_fields=["status"])

            # Create ServiceOrder
            ServiceOrder.objects.create(
                request=service_request,
                winning_offer=offer,
                provider=offer.provider,
                specialist=offer.proposed_specialist,
                start_date=service_request.start_date,
                end_date=service_request.end_date,
                man_days=service_request.expected_man_days,
                status="CREATED",
            )
        
        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, offer)

        return Response(
            {"detail": "Offer accepted and service order created."},
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        offer = self.get_object()

        if offer.status != OfferStatus.SUBMITTED:
            return Response(
                {"detail": "Only submitted offers can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offer.status = OfferStatus.REJECTED
        offer.save(update_fields=["status"])

        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, offer)

        return Response(
            {"detail": "Offer rejected."},
            status=status.HTTP_200_OK,
        )
