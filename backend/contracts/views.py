from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from .models import Contract, ContractVersion, PricingRule, ContractStatus
from .serializers import (
    ContractReadSerializer,
    ContractCreateSerializer,
    ContractVersionSerializer,
    PricingRuleSerializer,
)
from .permissions import IsContractCoordinator
from audit_log.utils import log_audit_event
from audit_log.models import AuditAction
from integrations.flowable_client import start_contract_negotiation
from service_requests.permissions import IsAuthenticatedOrFlowable


class ContractViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Contract.objects.select_related("provider")
    permission_classes = [IsAuthenticatedOrFlowable, IsContractCoordinator]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.is_superuser or getattr(self.request, "is_flowable", False):
            return self.queryset

        if user.provider_id:
            return self.queryset.filter(provider_id=user.provider_id)

        return self.queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ContractCreateSerializer
        return ContractReadSerializer

    # def get_permissions(self):
    #     if self.action in ["create", "metrics"]:
    #         return [IsAuthenticatedOrFlowable(), IsContractCoordinator()]
    #     return super().get_permissions()

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
        
        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, contract)

        # Start BPMN
        start_contract_negotiation(contract_id=contract.id)

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
        
        # AUDIT LOG
        log_audit_event(AuditAction.STATUS_CHANGE, contract)

        return Response({"status": "ACTIVE"})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        contract = self.get_object()

        if contract.status not in [ContractStatus.DRAFT, ContractStatus.IN_NEGOTIATION,]:
            return Response(
                {"detail": "Only draft or negotiated contracts can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.status = ContractStatus.REJECTED
        contract.save(update_fields=["status"])

        # Audit + notification automatically triggered
        log_audit_event(AuditAction.STATUS_CHANGE, contract)

        return Response({"status": "REJECTED"})

    @action(detail=False, methods=['get'], url_path='metrics')
    def metrics(self, request):
        """
        Get dashboard metrics for contract coordinator.
        Returns counts of contracts by status.
        """
        user = request.user
        
        # Define "expiring soon" threshold (e.g., 30 days)
        expiring_threshold = timezone.now() + timedelta(days=30)

        # Filter contracts that are pending, active, in negotiation, OR expiring soon
        contract_counts = self.get_queryset().aggregate(
            in_negotiation=Count('id', filter=Q(status='IN_NEGOTIATION')),
            pending_contracts=Count('id', filter=Q(status='PENDING')),
            active_contracts=Count('id', filter=Q(status='ACTIVE')),
            expiring_contracts=Count(
                'id', 
                filter=Q(
                    status='ACTIVE',
                    valid_to__lte=expiring_threshold,
                    valid_to__gte=timezone.now()
                )
            )
        )
        
        metrics_data = {
            "in_negotiation": contract_counts.get('in_negotiation', 0),
            "pending_contracts": contract_counts.get('pending_contracts', 0),
            "active_contracts": contract_counts.get('active_contracts', 0),
            "expiring_contracts": contract_counts.get('active_contracts', 0),
        }
        
        return Response(metrics_data, status=status.HTTP_200_OK)


class ContractVersionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ContractVersionSerializer
    permission_classes = [IsAuthenticated, IsContractCoordinator]

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
    permission_classes = [IsAuthenticated, IsContractCoordinator]

    def get_queryset(self):
        return PricingRule.objects.filter(
            contract_id=self.kwargs["contract_pk"]
        )

    def perform_create(self, serializer):
        serializer.save(contract_id=self.kwargs["contract_pk"])
