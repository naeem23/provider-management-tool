from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import *
from .serializers import *
from audit_log.models import AuditLog


# ====================
# SERVICE ORDER VIEWSET
# ====================
class ServiceOrderViewSet(viewsets.ModelViewSet):
    queryset = ServiceOrder.objects.all()
    # permission_classes = [IsAuthenticated]
    
    # Filterable fields
    filterset_fields = [
        'status',
        'supplier_name',
        'current_specialist_name',
        'role',
        'domain',
    ]
    
    # Searchable fields
    search_fields = [
        'id',
        'title',
        'current_specialist_name',
        'supplier_name',
    ]
    
    # Ordering
    ordering_fields = ['start_date', 'current_end_date', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceOrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceOrderUpdateSerializer
        return ServiceOrderDetailSerializer
    
    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        service_order = serializer.save(
            original_end_date=validated_data['current_end_date'],
            original_specialist_id=validated_data['current_specialist_id'],
            original_specialist_name=validated_data['current_specialist_name'],
            original_man_days=validated_data['current_man_days'],
        )
    
    @action(detail=True, methods=['get'])
    def extensions(self, request, pk=None):
        service_order = self.get_object()
        extensions = service_order.extensions.all()
        serializer = ExtensionDetailSerializer(extensions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def substitutions(self, request, pk=None):
        service_order = self.get_object()
        substitutions = service_order.substitutions.all()
        serializer = SubstitutionDetailSerializer(substitutions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        service_order = self.get_object()
        
        if service_order.status != 'ACTIVE':
            return Response(
                {'error': 'Only active service orders can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service_order.status = 'COMPLETED'
        service_order.actual_end_date = timezone.now().date()
        service_order.save()
        serializer = self.get_serializer(service_order)
        return Response(serializer.data)


