from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Contract, ContractVersion, ContractStatus
from .serializers import *
from .permissions import IsContractCoordinator
from audit_log.utils import serialize_for_json
from audit_log.models import AuditLog
from integrations.flowable_client import *
from integrations.third_party_service import third_party_service
from providers.models import Provider
from notifications.services import notify_roles


class ContractViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    # mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Contract.objects.select_related("provider")

    def get_queryset(self):
        user = self.request.user
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
            queryset = queryset.filter(status="ACTIVE", valid_till__range=(today, soon))

        elif search == "published-only":
            queryset = queryset.filter(Q(status='PUBLISHED') & (Q(external_id="") | Q(external_id__isnull=True)))

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return ContractCreateSerializer
        return ContractReadSerializer

    def get_permissions(self):
        if self.action in ["start_negotiation", "get_tasks", "accept_task", "reject_task", "counter_offer_task", "metrics", "retrieve"]:
            return [IsAuthenticated(), IsContractCoordinator()]
        return [AllowAny(),]

    def perform_create(self, serializer):
        specialist = serializer.validated_data.get("specialist")
        contract = serializer.save(provider=specialist.provider)

        # Broadcast notification
        notify_roles(
            role="CONTRACT_COORDINATOR",
            title="New Contract Created",
            message="A new contract has been created.",
            entity_type="Contract",
            entity_id=contract.id,
        )
        
    
    @action(detail=False, methods=["post"], url_path="update-status")
    def update_status(self, request):
        contract_id = request.data.get("contract_id")
        contract_status = request.data.get("status")

        if not contract_id or not contract_status:
            return Response(
                {"detail": "contract_id and status are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if contract_status not in ["ACTIVE", "REJECTED"]:
            return Response(
                {"detail": "Valid status are ACTIVE/REJECTED."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch contract
        contract = get_object_or_404(
            Contract,
            external_id=contract_id
        )

        contract.status = contract_status
        contract.save(update_fields=["status"])

        # Notification
        notify_roles(
            role="CONTRACT_COORDINATOR",
            title="Contract Status Updated",
            message=f"Contract status changed to {contract.status}.",
            entity_type="Contract",
            entity_id=contract.id,
        )
        
        return Response(
            {
                "message": "Contract status updated successfully.",
                "contract_id": str(contract.external_id),
                "status": contract.status,
            },
            status=status.HTTP_200_OK,
        )


    @action(detail=True, methods=["post"], url_path="start-negotiation")
    def start_negotiation(self, request, pk=None):
        """
        Start negotiation for a contract
        
        Steps:
        1. Validate contract can be negotiated
        2. Update contract in local database with status "In Negotiation"
        3. Update contract status in 3rd party API
        4. Create Flowable task for contract_coordinator group
        """

        try:
            # Step 1: Get contract
            contract = self.get_object()
            
            # Validate contract can be negotiated
            if contract.status == 'IN_NEGOTIATION':
                return Response(
                    {'error': 'Contract is already in negotiation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if contract.status in ['ACTIVE', 'REJECTED', 'EXPIRED']:
                return Response(
                    {'error': 'Contract cannot be negotiated in current status'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # TODO: Step 3: Update 3rd party API
            # try:
            #     third_party_service.update_contract_status(
            #         external_id=external_id,
            #         status='In Negotiation'
            #     )
            # except Exception as e:
            #     raise Exception(f"Failed to update 3rd party API: {str(e)}")

            # Step 4: Create Flowable task
            contract_data = {
                'contract_id': str(contract.id),
                'title': contract.title,
                'specialist_name': contract.specialist.full_name,
                'proposed_rate': str(contract.proposed_rate),
                'providers_expected_rate': str(contract.providers_expected_rate) if contract.providers_expected_rate else "0.00",
                'valid_from': contract.valid_from,
                'valid_till': contract.valid_till,
                'response_deadline': contract.response_deadline,
            }
            print('.......................... i am here......................')
                
            try:
                start_contract_negotiation(contract_data=contract_data)
            except Exception as e:
                raise Exception(f"Failed to create Flowable task: {str(e)}")
                
            print('.......................... i am here 2......................')

            contract.status = 'IN_NEGOTIATION'
            contract.save()

            AuditLog.log_action(
                user=request.user,
                action_type='CONTRACT_NEGOTIATION_STARTED',
                action_category='CONTRACT_MANAGEMENT',
                description=f'Negotiation started for contract {str(contract.id)}',
                entity_type='Contract',
                entity_id=contract.id,
                metadata={
                    'contract_title': contract.title,
                    'status': contract.status
                },
                request=request
            )

            # Step 5: Return success response
            return Response({
                'message': 'Contract and task created successfully',
                'contract_id': str(contract.id),
                'status': contract.status
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to start negotiation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['get'], url_path='tasks')
    def get_tasks(self, request):
        """
        Get all negotiation tasks for contract_coordinator group
        """
        group_id = 'contract_coordinator'
        
        try:
            # Step 1: Get tasks from Flowable
            flowable_tasks = get_tasks_by_group(group_id=group_id)
            
            # Step 2: Enrich with contract details from local database
            tasks_with_contracts = []
            
            for task in flowable_tasks:
                contract_id = task['variables'].get('contract_id')
                
                if not contract_id:
                    continue
                
                try:
                    # Get contract from database
                    contract = Contract.objects.get(id=contract_id)
                    latest_versions = contract.versions.order_by('-version_number').first()
                    proposed_rate = str(contract.proposed_rate)
                    if latest_versions:
                        proposed_rate = str(latest_versions.counter_rate)

                    task_data = {
                        'task_id': task['task_id'],
                        'task_name': task['task_name'],
                        'created_time': task['created_time'],
                        'contract': {
                            'id': contract.id,
                            'external_id': contract.external_id,
                            'title': contract.title,
                            'specialist': contract.specialist.full_name,
                            'proposed_rate': proposed_rate,
                            'providers_expected_rate': str(contract.providers_expected_rate),
                            'valid_from': contract.valid_from,
                            'valid_till': contract.valid_till,
                            'response_deadline': contract.response_deadline,
                            'status': contract.status,
                            'domain': getattr(contract, 'domain', ''),
                            'terms_condition': getattr(contract, 'terms_condition', ''),
                        }
                    }
                    
                    tasks_with_contracts.append(task_data)
                    
                except Contract.DoesNotExist:
                    return Response({'error': 'Contract not found'}, status=status.HTTP_404_NOT_FOUND)
                        
            return Response({
                'count': len(tasks_with_contracts),
                'tasks': tasks_with_contracts
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve tasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    

    @action(detail=False, methods=['post'], url_path='tasks/(?P<task_id>[^/.]+)/accept')
    def accept_task(self, request, task_id=None):
        """
        Accept a contract negotiation task
        
        Steps:
        1. Validate task exists in Flowable
        2. Get contract_id from task variables
        3. Update contract status to "Accepted"
        4. Complete Flowable task with action="accept"
        5. Update 3rd party API
        """
        try:
            # Step 1: Get task details from Flowable
            try:
                task_info = get_task_variable(task_id=task_id)
            except Exception as e:
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contract_id = task_info['variables'].get('contract_id')
            
            if not contract_id:
                return Response(
                    {'error': 'Task does not have contract_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Step 2: Update contract status in database
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                return Response(
                    {'error': 'Contract not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Step 3: Complete Flowable task
            try:
                complete_task(
                    task_id=task_id,
                    action='accept'
                )
            except Exception as e:
                raise Exception(f"Failed to complete task: {str(e)}")
                
            # TODO: Step 4: Update 3rd party API
            # try:
            #     third_party_service.update_contract_status(
            #         external_id=contract.external_id,
            #         status='Accepted'
            #     )
            # except Exception as e:
            #     raise Exception(f"Failed to update 3rd party API: {str(e)}")

            latest_versions = contract.versions.order_by('-version_number').first()
            proposed_rate = contract.proposed_rate
            if latest_versions:
                proposed_rate = latest_versions.counter_rate

            contract.status = 'ACTIVE'
            contract.negotiated_rate = proposed_rate
            contract.save()

            AuditLog.log_action(
                user=request.user,
                action_type='CONTRACT_ACCEPTED',
                action_category='CONTRACT_MANAGEMENT',
                description=f'Accepted contract {str(contract.id)}',
                entity_type='Contract',
                entity_id=contract.id,
                metadata={
                    'contract_title': contract.title,
                },
                request=request
            )
            
            # Step 5: Return success response
            return Response({
                'message': 'Contract accepted successfully',
                'contract_id': str(contract.id),
                'status': contract.status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to accept contract: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['post'], url_path='tasks/(?P<task_id>[^/.]+)/reject')
    def reject_task(self, request, task_id=None):
        """
        Reject a contract negotiation task
        
        Steps:
        1. Validate task exists in Flowable
        2. Get contract_id from task variables
        3. Update contract status to "Rejected"
        4. Complete Flowable task with action="reject"
        5. Update 3rd party API
        """
        try:
            # Step 1: Get task details from Flowable
            try:
                task_info = get_task_variable(task_id=task_id)
            except Exception as e:
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contract_id = task_info['variables'].get('contract_id')
            
            if not contract_id:
                return Response(
                    {'error': 'Task does not have contract_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Step 2: Update contract status in database
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                return Response(
                    {'error': 'Contract not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contract.status = 'REJECTED'
            contract.save()
                        
            # Step 3: Complete Flowable task
            try:
                complete_task(
                    task_id=task_id,
                    action='reject'
                )
            except Exception as e:
                raise Exception(f"Failed to complete task: {str(e)}")
            
            # TODO: Step 4: Update 3rd party API
            # try:
            #     third_party_service.update_contract_status(
            #         external_id=contract.external_id,
            #         status='Rejected'
            #     )
            # except Exception as e:
            #     raise Exception(f"Failed to update 3rd party API: {str(e)}")

            AuditLog.log_action(
                user=request.user,
                action_type='CONTRACT_REJECTED',
                action_category='CONTRACT_MANAGEMENT',
                description=f'Rejected contract {str(contract.id)}',
                entity_type='Contract',
                entity_id=contract.id,
                metadata={
                    'contract_title': contract.title,
                },
                request=request
            )
            
            # Step 5: Return success response
            return Response({
                'message': 'Contract rejected successfully',
                'contract_id': str(contract.id),
                'status': contract.status
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to reject contract: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['post'], url_path='tasks/(?P<task_id>[^/.]+)/counter-offer')
    def counter_offer_task(self, request, task_id=None):
        """
        Submit counter offer for a contract negotiation task
        
        Request Body:
        {
            "counter_rate": 6500.00,
            "counter_explanation": "Based on market rates and expertise",
            "counter_terms": "Net 30 payment terms"
        }
        
        Steps:
        1. Validate input data
        2. Validate task exists in Flowable
        3. Get contract_id from task variables
        4. Create ContractVersion record
        5. Update contract status to "Counter Offer Submitted"
        6. Complete Flowable task with action="counter_offer"
        7. Update 3rd party API
        """
        # Step 1: Validate input data
        serializer = CounterOfferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            # Step 2: Get task details from Flowable
            try:
                task_info = get_task_variable(task_id=task_id)
            except Exception as e:
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            contract_id = task_info['variables'].get('contract_id')
            
            if not contract_id:
                return Response(
                    {'error': 'Task does not have contract_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Step 3: Get contract from database
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                return Response(
                    {'error': 'Contract not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if contract.status != "IN_NEGOTIATION":
                return Response(
                    {'error': 'Counter offer is possible only for contract in negotiation'},
                    status=status.HTTP_400_BAD_REQUEST
                )
             
            # Step 4: create latest version
            latest_version = ContractVersion.objects.filter(
                contract=contract
            ).order_by('-version_number').first()
                
            next_version = 1 if not latest_version else latest_version.version_number + 1
                
            contract_version = ContractVersion.objects.create(
                contract=contract,
                version_number=next_version,
                counter_rate=validated_data['counter_rate'],
                counter_offer_explanation=validated_data['counter_explanation'],
                proposed_terms_and_condition=validated_data['counter_terms'],
            )
            
            # Step 6: Complete Flowable task
            try:
                complete_task(
                    task_id=task_id,
                    action='counter_offer',
                    variables={
                        'contract_id': str(contract.id),
                        'version_id': str(contract_version.id),
                        'counter_rate': float(validated_data['counter_rate']),
                        'counter_explanation': validated_data['counter_explanation'],
                        'counter_terms': validated_data['counter_terms']
                    }
                )
            except Exception as e:
                raise Exception(f"Failed to complete task: {str(e)}")
            
            # TODO: Step 7: Update 3rd party API
            # try:
            #     third_party_service.update_contract_status(
            #         external_id=contract.external_id,
            #         status='Counter Offer Submitted'
            #     )
            #     logger.info(f"3rd party API updated for contract {contract.external_id}")
            # except Exception as e:
            #     logger.error(f"3rd party API update failed: {str(e)}")
            #     raise Exception(f"Failed to update 3rd party API: {str(e)}")

            AuditLog.log_action(
                user=request.user,
                action_type='CONTRACT_COUNTER_OFFER',
                action_category='CONTRACT_MANAGEMENT',
                description=f'Counter offer submitted for contract {str(contract.id)}',
                entity_type='Contract',
                entity_id=contract.id,
                metadata={
                    'contract_title': contract.title,
                    'contract_version_id': str(contract_version.id),
                    'counter_rate': str(contract_version.counter_rate),
                },
                request=request
            )
            
            # Step 8: Return success response
            return Response({
                'message': 'Counter offer submitted successfully',
                'contract_id': str(contract.id),
                'status': contract.status,
                'version_number': next_version,
                'counter_rate': str(validated_data['counter_rate'])
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to submit counter offer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['get'], url_path='metrics')
    def metrics(self, request):
        """
        Get dashboard metrics for contract coordinator.
        Returns counts of contracts by status.
        """
        user = request.user
        
        # Define "expiring soon" threshold (e.g., 30 days)
        today = timezone.now()
        soon = today + timedelta(days=30)

        # Filter contracts that are pending, active, in negotiation, OR expiring soon
        contract_counts = self.get_queryset().aggregate(
            in_negotiation=Count('id', filter=Q(status='IN_NEGOTIATION')),
            rejected_contracts=Count('id', filter=Q(status='REJECTED')),
            active_contracts=Count('id', filter=Q(status='ACTIVE')),
            expiring_contracts=Count(
                'id', 
                filter=Q(
                    status='ACTIVE',
                    valid_till__range=(today, soon),
                )
            )
        )
        
        metrics_data = {
            "in_negotiation": contract_counts.get('in_negotiation', 0),
            "rejected_contracts": contract_counts.get('rejected_contracts', 0),
            "active_contracts": contract_counts.get('active_contracts', 0),
            "expiring_contracts": contract_counts.get('expiring_contracts', 0),
        }
        
        return Response(metrics_data, status=status.HTTP_200_OK)


class ContractVersionViewSet(viewsets.ModelViewSet):
    queryset = ContractVersion.objects.select_related("contract")
    serializer_class = ContractVersionSerializer
    permission_classes = [IsAuthenticated,]

    def get_queryset(self):
        return ContractVersion.objects.filter(
            contract_id=self.kwargs["contract_pk"]
        ).order_by("-version_number")

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny(),]
        
        return [IsAuthenticated(),]


    def create(self, request, *args, **kwargs):
        # Step 1: Validate input data
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contract = get_object_or_404(Contract, id=self.kwargs["contract_pk"])

        if contract.status in ['ACTIVE', 'REJECTED', 'EXPIRED']:
            return Response(
                {'error': 'Contract cannot be negotiated in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        latest_version = ContractVersion.objects.filter(contract=contract).order_by('-version_number').first()
        next_version = 1 if not latest_version else latest_version.version_number + 1
        
        version = serializer.save(contract=contract, version_number=next_version)
        
        # Step 4: Create Flowable task
        try:
            contract_data = {
                'contract_id': str(contract.id),
                'title': contract.title,
                'specialist_name': contract.specialist.full_name,
                'proposed_rate': str(version.counter_rate),
                'providers_expected_rate': str(latest_version.counter_rate) if latest_version else "0.00",
                'valid_from': contract.valid_from,
                'valid_till': contract.valid_till,
                'response_deadline': contract.response_deadline,
            }
            
            flowable_result = start_contract_negotiation(contract_data=contract_data)
            
            return Response({
                'message': 'Contract version and task created successfully',
                'contract_id': str(contract.id),
                'version_id': str(version.id),
                'status': contract.status
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create Flowable task: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )