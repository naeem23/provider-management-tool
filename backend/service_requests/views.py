from django.db.models import Count
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ServiceRequest, RequestStatus
from .serializers import (
    ServiceRequestReadSerializer,
    ServiceRequestCreateSerializer,
    ServiceRequestUpdateSerializer,
)
from .permissions import CanManageServiceRequest, CanEditServiceRequest


class ServiceRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Service Request API.
    """

    queryset = ServiceRequest.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            ServiceRequest.objects
            .annotate(offers_count=Count("offers"))
            .order_by("-created_at")
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ServiceRequestCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ServiceRequestUpdateSerializer
        return ServiceRequestReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanManageServiceRequest()]
        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), CanManageServiceRequest(), CanEditServiceRequest()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        """
        Open request for bidding (Flowable will hook here later).
        """
        service_request = self.get_object()

        if service_request.status != RequestStatus.IMPORTED:
            return Response(
                {"detail": "Only imported requests can be opened."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.status = RequestStatus.OPEN
        service_request.save(update_fields=["status"])

        return Response({"status": "OPEN"})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Close request for bidding.
        """
        service_request = self.get_object()

        if service_request.status != RequestStatus.OPEN:
            return Response(
                {"detail": "Only open requests can be closed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service_request.status = RequestStatus.CLOSED
        service_request.save(update_fields=["status"])

        return Response({"status": "CLOSED"})
