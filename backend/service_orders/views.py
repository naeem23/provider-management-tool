from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ServiceOrder, OrderStatus
from .serializers import (
    ServiceOrderReadSerializer,
    ServiceOrderCreateSerializer,
    SubstitutionRequestSerializer,
    ExtensionRequestSerializer,
)
from .permissions import (
    CanViewOrder,
    CanManageOrder,
    CanRequestSubstitution,
    CanRequestExtension,
)
from audit_log.models import AuditLog


class ServiceOrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ServiceOrder.objects.select_related(
        "provider", "specialist", "winning_offer"
    )
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return self.queryset

        if user.provider_id:
            return self.queryset.filter(provider_id=user.provider_id)

        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ServiceOrderCreateSerializer
        return ServiceOrderReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanManageOrder()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        order = self.get_object()

        if order.status != OrderStatus.CREATED:
            return Response(
                {"detail": "Order can only be started from CREATED state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = OrderStatus.IN_PROGRESS
        order.save(update_fields=["status"])

        return Response({"status": "IN_PROGRESS"})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        order = self.get_object()

        if order.status != OrderStatus.IN_PROGRESS:
            return Response(
                {"detail": "Only in-progress orders can be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = OrderStatus.COMPLETED
        order.save(update_fields=["status"])

        return Response({"status": "COMPLETED"})


class SubstitutionRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubstitutionRequestSerializer
    permission_classes = [IsAuthenticated, CanRequestSubstitution]

    def get_queryset(self):
        return self.request.user.provider.service_orders.all()

    def perform_create(self, serializer):
        serializer.save(
            requested_by=self.request.user,
            status="REQUESTED",
        )


class ExtensionRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExtensionRequestSerializer
    permission_classes = [IsAuthenticated, CanRequestExtension]

    def get_queryset(self):
        return self.request.user.provider.service_orders.all()

    def perform_create(self, serializer):
        serializer.save(
            requested_by=self.request.user,
            status="REQUESTED",
        )
