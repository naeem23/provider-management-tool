from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Contract, ContractVersion, PricingRule, ContractStatus
from .serializers import (
    ContractReadSerializer,
    ContractCreateSerializer,
    ContractVersionSerializer,
    PricingRuleSerializer,
)
from .permissions import CanManageContracts, CanApproveContract


class ContractViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Contract.objects.select_related("provider")
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
            return ContractCreateSerializer
        return ContractReadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanManageContracts()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def start_negotiation(self, request, pk=None):
        contract = self.get_object()

        if contract.status != ContractStatus.DRAFT:
            return Response(
                {"detail": "Only draft contracts can enter negotiation."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.status = ContractStatus.IN_NEGOTIATION
        contract.save(update_fields=["status"])
        return Response({"status": "IN_NEGOTIATION"})

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        contract = self.get_object()

        if contract.status != ContractStatus.IN_NEGOTIATION:
            return Response(
                {"detail": "Only negotiated contracts can be activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.status = ContractStatus.ACTIVE
        contract.save(update_fields=["status"])
        return Response({"status": "ACTIVE"})


class ContractVersionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ContractVersionSerializer
    permission_classes = [IsAuthenticated, CanManageContracts]

    def get_queryset(self):
        return ContractVersion.objects.filter(
            contract_id=self.kwargs["contract_pk"]
        ).order_by("-version_number")

    def perform_create(self, serializer):
        contract = Contract.objects.get(pk=self.kwargs["contract_pk"])
        last_version = (
            ContractVersion.objects.filter(contract=contract)
            .order_by("-version_number")
            .first()
        )

        next_version = 1 if not last_version else last_version.version_number + 1

        serializer.save(
            contract=contract,
            version_number=next_version,
            created_by=self.request.user,
        )


class PricingRuleViewSet(viewsets.ModelViewSet):
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAuthenticated, CanManageContracts]

    def get_queryset(self):
        return PricingRule.objects.filter(
            contract_id=self.kwargs["contract_pk"]
        )

    def perform_create(self, serializer):
        serializer.save(contract_id=self.kwargs["contract_pk"])
