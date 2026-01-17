from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from .models import AuditLog
from .serializers import AuditLogSerializer
from .permissions import CanViewAuditLogs

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    # Filterable fields
    filterset_fields = ['action_category', 'action_type', 'user', 'result', 'user_role']
    
    # Searchable fields
    search_fields = ['description', 'entity_id', 'user__username']
    
    # Ordering
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter logs based on user's company
        """
        user = self.request.user
        
        # Provider Admin can see all logs for their company
        if user.role == 'PROVIDER_ADMIN':
            return AuditLog.objects.filter(user__provider=user.provider)
        
        # Other users can only see their own logs
        return AuditLog.objects.filter(user=user)
