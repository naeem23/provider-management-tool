from django.db.models import Count
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import ServiceRequest, RequestStatus, ServiceOffer
from .serializers import ServiceRequestSerializer
from .offer_serializers import ServiceOfferCreateSerializer
from .permissions import IsSupplierRep
from audit_log.utils import log_audit_event
from audit_log.models import AuditAction
from integrations.flowable_client import *
from notifications.services import notify_roles
from providers.models import Provider
from specialists.models import Specialist


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
    serializer_class = ServiceRequestSerializer

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

    def get_permissions(self):
        if self.action == "generate":
            return [AllowAny(),]
        elif self.action in ["create", "update", "partial_update"]:
            return [IsAuthenticated(), IsSupplierRep()]
        elif self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [AllowAny()]


    @action(detail=False, methods=["post"])
    def generate(self, request):
        """
        Create a Service Request
        
        Steps:
        1. Validate service request exists by filtering external_id
        2. validate service request status is open
        3. Create service request in local database with status "Open"
        4. Create Flowable task for supplier_rep group
        """
    
        # Step 1: Validate input data
        serializer = ServiceRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        external_id = validated_data.get('external_id')
        request_status = validated_data.get('status')

        if request_status.lower() != 'open':
            return Response(
                {"details": "Only Open Service Requests are accepted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 2: Get or create service request
            service_request, created = ServiceRequest.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'title': validated_data.get('title'),
                    'role_name': validated_data.get('role_name'),
                    'technology': validated_data.get('technology'),
                    'specialization': validated_data.get('specialization'),
                    'experience_level': validated_data.get('experience_level'),
                    'start_date': validated_data.get('start_date'),
                    'end_date': validated_data.get('end_date'),
                    'expected_man_days': validated_data.get('expected_man_days'),
                    'criteria_json': validated_data.get('criteria_json'),
                    'task_description': validated_data.get('task_description'),
                    'offer_deadline': validated_data.get('offer_deadline'),
                    'word_mode': validated_data.get('word_mode'),
                }
            )

            # If service_request already exists, update it
            if not created:
                service_request.title = validated_data.get('title')
                service_request.role_name =validated_data.get('role_name'),
                service_request.technology = validated_data.get('technology'),
                service_request.specialization = validated_data.get('specialization'),
                service_request.experience_level = validated_data.get('experience_level'),
                service_request.start_date = validated_data.get('start_date'),
                service_request.end_date = validated_data.get('end_date'),
                service_request.expected_man_days = validated_data.get('expected_man_days'),
                service_request.criteria_json = validated_data.get('criteria_json'),
                service_request.task_description = validated_data.get('task_description'),
                service_request.offer_deadline = validated_data.get('offer_deadline'),
                service_request.word_mode = validated_data.get('word_mode'),

            service_request.status = 'OPEN'
            service_request.save()

            # Step 4: Create Flowable task
            try:
                flowable_result = generate_request_task(request_id=str(service_request.id))
                
            except Exception as e:
                raise Exception(f"Failed to create Flowable task: {str(e)}")

            # Notification Create 
            notify_roles(
                role="SUPPLIER_REP",
                title="New Service Request",
                message="A new service request has been created.",
                entity_type="ServiceRequest",
                entity_id=service_request.id,
            )

            # Step 5: Return success response
            return Response({
                'message': 'Contract and task created successfully',
                'contract_id': service_request.id,
                'status': service_request.status
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to start negotiation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['get'], url_path='tasks')
    def get_tasks(self, request):
        """
        Get all negotiation tasks for supplier_rep group
        """
        group_id = 'supplier_rep'
        
        try:
            # Step 1: Get tasks from Flowable
            flowable_tasks = get_tasks_by_group(group_id=group_id)
            
            # Step 2: Enrich with contract details from local database
            tasks_with_request = []
            
            for task in flowable_tasks:
                request_id = task['variables'].get('request_id')
                
                if not request_id:
                    continue
                
                try:
                    # Get contract from database
                    service_request = ServiceRequest.objects.get(id=request_id)
                    
                    task_data = {
                        'task_id': task['task_id'],
                        'task_name': task['task_name'],
                        'created_time': task['created_time'],
                        'service_request': {
                            'id': service_request.id,
                            'external_id': service_request.external_id,
                            'title': service_request.title,
                            'role_name': service_request.role_name,
                            'technology': service_request.technology,
                            'specialization': service_request.specialization,
                            'experience_level': service_request.experience_level,
                            'start_date': service_request.start_date,
                            'end_date': service_request.end_date,
                            'expected_man_days': service_request.expected_man_days,
                            'criteria_json': service_request.criteria_json,
                            'task_description': service_request.task_description,
                            'offer_deadline': service_request.offer_deadline,
                            'word_mode': service_request.word_mode,
                        }
                    }
                    
                    tasks_with_request.append(task_data)
                    
                except Contract.DoesNotExist:
                    continue
                        
            return Response({
                'count': len(tasks_with_request),
                'tasks': tasks_with_request
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve tasks: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=False, methods=['post'], url_path='tasks/(?P<task_id>[^/.]+)/submit-offer')
    def submit_offer_task(self, request, task_id=None):
        """
        Submit offer for a service request task
        
        Request Body:
        {
            "request": '',
            "provider": '',
            "proposed_specialist": '', 
            "daily_rate": 650.00,
            "travel_cost": 10.00,
            "total_cost": 670.00
            "notes": ''
        }
        
        Steps:
        1. Validate input data
        2. Validate task exists in Flowable
        3. Get request_id from task variables
        4. Create ServiceOffer record
        5. Complete Flowable task with action="submit_offer"
        """
        # Step 1: Validate input data
        serializer = ServiceOfferCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        service_request = validated_data.get('request')
        provider = validated_data.get('provider')
        specialist = validated_data.get('proposed_specialist')
        
        try:
            if not service_request:
                return Response(
                    {'error': 'Service request id is missing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not provider:
                return Response(
                    {'error': 'Provider id is missing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not specialist:
                return Response(
                    {'error': 'Specialist id is missing'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if service_request.status != "OPEN":
                return Response(
                    {'error': 'Service offer is possible only for open service request'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            offer = ServiceOffer.objects.create(
                request=service_request,
                provider=provider,
                proposed_specialist=specialist,
                daily_rate=validated_data['daily_rate'],
                travel_cost=validated_data['travel_cost'],
                total_cost=validated_data['total_cost'],
                notes=validated_data['notes'],
            )

            # TODO: Step 3: Submit offer to third party
            # try:
            #     third_party_service.update_contract_status(
            #         external_id=external_id,
            #         status='In Negotiation'
            #     )
            # except Exception as e:
            #     raise Exception(f"Failed to update 3rd party API: {str(e)}")
            
            # Step 5: Complete Flowable task
            try:
                complete_task(
                    task_id=task_id,
                    action='submit_offer',
                    variables={
                        'offer_id': str(offer.id),
                    }
                )
            except Exception as e:
                raise Exception(f"Failed to complete task: {str(e)}")
            
            # Step 6: Return success response
            return Response({
                'message': 'Counter offer submitted successfully',
                'offer_id': str(offer.id),
                'daily_rate': str(validated_data['daily_rate']),
                'travel_cost': str(validated_data['travel_cost']),
                'total_cost': str(validated_data['total_cost']),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to submit counter offer: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )