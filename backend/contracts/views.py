from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Contract, ContractVersion, ContractStatus
from .serializers import (
    ContractReadSerializer,
    ContractCreateSerializer,
    ContractVersionSerializer,
)
from .permissions import IsContractCoordinator
from audit_log.utils import log_audit_event
from audit_log.models import AuditAction
from integrations.flowable_client import start_contract_negotiation
from integrations.flowable_contract_service import flowable_contract_service
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
        excluded_statuses = [
            "ACTIVE",
            "REJECTED",
            "EXPIRED",
        ]
        queryset = self.queryset

        # ---- role-based filtering ----
        if not (user.is_staff or user.is_superuser or getattr(self.request, "is_flowable", False)):
            if user.provider_id:
                queryset = queryset.filter(provider_id=user.provider_id)
            else:
                return queryset.none()

        # ---- search-based filtering (NEW) ----
        search = self.request.query_params.get("q")

        if search == "active":
            queryset = queryset.filter(status="ACTIVE")

        elif search == "expiring":
            today = timezone.now()
            soon = today + timedelta(days=30)

            queryset = queryset.filter(
                status="ACTIVE",
                valid_to__range=(today, soon)
            )

        elif search == "published-only":
            queryset = queryset.exclude(status__in=excluded_statuses)

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ContractCreateSerializer
        return ContractReadSerializer

    # @action(detail=True, methods=["get"], url_path="start-negotiation")
    # def start_negotiation(self, request, pk=None):
    #     contract = self.get_object()

    #     if contract.status != ContractStatus.PENDING:
    #         return Response(
    #             {"detail": "Only draft contracts can enter negotiation."},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     contract.status = ContractStatus.IN_NEGOTIATION
    #     contract.save(update_fields=["status"])
        
    #     # AUDIT LOG
    #     log_audit_event(AuditAction.STATUS_CHANGE, contract)

    #     # Start BPMN
    #     start_contract_negotiation(contract_id=contract.id)

    #     return Response({"status": "IN_NEGOTIATION"})

    @action(detail=False, methods=["post"], url_path="start-negotiation")
    def start_negotiation(self, request):
        """
        Start negotiation for a contract
        
        Steps:
        1. Validate contract exists and can be negotiated
        2. Create/Update contract in local database with status "In Negotiation"
        3. Update contract status in 3rd party API
        4. Create Flowable task for contract_coordinator group
        5. Save task reference in NegotiationTask table
        """
    
        try:
            payload = request.data

            # Step 1: Get or create contract in local database
            contract = get_object_or_404(Contract, external_id=payload["contract_id"])
            
            # Validate contract can be negotiated
            if contract.status == 'IN_NEGOTIATION':
                return Response(
                    {'error': 'Contract is already in negotiation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if contract.status in ['ACTIVE', 'EXPIRED', 'REJECTED']:
                return Response(
                    {'error': 'Contract cannot be negotiated in current status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                # Step 2: Update contract status to "In Negotiation"
                contract.status = 'IN_NEGOTIATION'
                contract.save()
                
                try:
                    # Step 3: Update 3rd party API
                    third_party_response = third_party_service.update_contract_status(
                        external_id=contract.external_id,
                        status='In Negotiation'
                    )
                                        
                except Exception as e:
                    # Rollback will happen automatically
                    raise Exception(f"Failed to update 3rd party API: {str(e)}")
                
                try:
                    # Step 4: Prepare contract data for Flowable
                    contract_data = {
                        'contract_id': contract.id,
                        'title': contract.title,
                        'specialist_name': contract.specialist,
                        'proposed_rate': float(contract.offered_daily_rate),
                        'expected_rate': float(contract.expected_rate),
                        'valid_from': contract.valid_from,
                        'valid_till': contract.valid_to,
                        'response_deadline': contract.response_deadline,
                    }
                    
                    # Start Flowable process
                    flowable_result = flowable_contract_service.start_process(contract_data)
                                        
                    # Step 5: Get the created task
                    tasks = flowable_contract_service.get_tasks_by_group('contract_coordinator')
                    
                    # Find the task for this contract
                    contract_task = None
                    for task in tasks:
                        if task['variables'].get('contract_id') == contract.id:
                            contract_task = task
                            break
                    
                    if not contract_task:
                        raise Exception("Task not found after process start")
                    
                    # Save task reference in NegotiationTask table
                    negotiation_task = NegotiationTask.objects.create(
                        contract=contract,
                        flowable_task_id=contract_task['task_id'],
                        flowable_process_instance_id=flowable_result['process_instance_id'],
                        group_id='contract_coordinator',
                        status='Active',
                        created_by=request.user
                    )
                                        
                except Exception as e:
                    # Rollback will happen automatically
                    raise Exception(f"Failed to create Flowable task: {str(e)}")
            
            # Step 6: Return success response
            return Response({
                'message': 'Negotiation started successfully',
                'contract_id': contract.id,
                'external_id': contract.external_id,
                'status': contract.status,
                'task_id': contract_task['task_id'],
                'process_instance_id': flowable_result['process_instance_id'],
                'group_id': 'contract_coordinator'
            }, status=status.HTTP_201_CREATED)
            
        except Contract.DoesNotExist:
            return Response(
                {'error': 'Contract not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {'error': f'Failed to start negotiation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

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


class ContractVersionViewSet(viewsets.ModelViewSet):
    queryset = ContractVersion.objects.select_related("contract")
    serializer_class = ContractVersionSerializer
    permission_classes = [IsAuthenticated, IsContractCoordinator]

    def get_queryset(self):
        return ContractVersion.objects.filter(
            contract_id=self.kwargs["contract_pk"]
        ).order_by("-version_number")

    def perform_create(self, serializer):
        contract = get_object_or_404(
            Contract,
            id=self.kwargs["contract_pk"]
        )

        with transaction.atomic():
            last_version = (
                ContractVersion.objects
                .filter(contract=contract)
                .order_by("-version_number")
                .first()
            )

            next_version = (
                last_version.version_number + 1
                if last_version
                else 1
            )

            serializer.save(
                contract=contract,
                version_number=next_version
            )