from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
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
    IsAuthenticatedOrFlowable,
)
from audit_log.utils import log_audit_event
from audit_log.models import AuditAction
from specialists.models import Specialist
from accounts.models import User, UserRole


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
    permission_classes = [IsAuthenticatedOrFlowable]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser or getattr(self.request, "is_flowable", False):
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
            return [IsAuthenticatedOrFlowable(), IsSupplierRep()]
        if self.action in ["update", "partial_update"]:
            return [IsAuthenticatedOrFlowable(), IsSupplierRep(), CanEditDraftOffer()]
        if self.action in ["accept", "reject"]:
            return [IsAuthenticatedOrFlowable(), CanDecideOffer()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        specialist = serializer.validated_data.get("proposed_specialist")

        if not specialist:
            raise ValidationError("No specialist/provider found")

        # Flowable-triggered request
        if getattr(request, "is_flowable", False):
            submitted_by = User.objects.filter(
                provider=specialist.provider,
                role=UserRole.SUPPLIER_REP
            ).first()

            if not submitted_by:
                raise ValidationError(
                    "No supplier representative found for this provider"
                )

            offer = serializer.save(
                provider=specialist.provider,
                submitted_by=submitted_by,
                status=OfferStatus.DRAFT,
            )
        else:
            # Normal user request
            offer = serializer.save(
                provider=specialist.provider,
                submitted_by=request.user,
                status=OfferStatus.DRAFT,
            )

        # IMPORTANT: return serialized offer with ID
        response_serializer = ServiceOfferReadSerializer(offer)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
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

        #TODO: Maybe need to check if proposed_specialist.provider != authenticated_provider
        # reject offer.

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
