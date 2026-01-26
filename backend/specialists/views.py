from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Specialist
from .serializers import SpecialistSerializer
from providers.permissions import IsProviderAdmin
from audit_log.models import AuditLog
from audit_log.utils import serialize_for_json


class SpecialistViewSet(viewsets.ModelViewSet):
    """
    CRUD API for managing specialists.
    Provider Admins and Specialist managers can update specialists.
    """
    queryset = Specialist.objects.all()
    serializer_class = SpecialistSerializer
    permission_classes = [IsAuthenticated,]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsProviderAdmin()]
        return [AllowAny()]

    def get_queryset(self):
        user = self.request.user

        queryset = self.queryset

        if user.is_staff or user.is_superuser:
            return queryset.order_by("-created_at")

        
        search = self.request.query_params.get("q")
        if search:
            queryset = queryset.filter(status="Active").filter(
                Q(role_name__icontains=search) |
                Q(experience_level__icontains=search) |
                Q(skills__icontains=search) |
                Q(languages_spoken__icontains=search) |
                Q(specialization__icontains=search) |
                Q(certifications__icontains=search)
            )
            return queryset.order_by("-created_at")

        return queryset.filter(provider=user.provider).order_by("-created_at")

    def perform_create(self, serializer):
        # Auto-assign provider based on logged-in user
        specialist = serializer.save(provider=self.request.user.provider)
        
        AuditLog.log_action(
            user=self.request.user,
            action_type='SPECIALIST_CREATED',
            action_category='SPECIALIST_MANAGEMENT',
            description=f'Create a new specialist: {str(specialist.id)}',
            entity_type='Specialists',
            entity_id=specialist.id,
            metadata={
                'first_name': specialist.first_name,
                'last_name': specialist.last_name,
            },
        )

    def perform_update(self, serializer):
        old_data = serialiserialize_for_json(self.get_object())
        specialist = serializer.save(provider=self.request.user.provider)
        AuditLog.log_action(
            user=self.request.user,
            action_type='SPECIALIST_UPDATED',
            action_category='SPECIALIST_MANAGEMENT',
            description=f'Specialist {specialist.first_name} updated',
            entity_type='Specialists',
            entity_id=specialist.id,
            metadata={
                'old_data': {
                    **old_data
                },
                'new_data': {
                    **specialist
                },
            },
        )
    
    def perform_destroy(self, instance):
        AuditLog.log_action(
            user=self.request.user,
            action_type='SPECIALIST_DELETED',
            action_category='SPECIALIST_MANAGEMENT',
            description=f'Specialist with ID {str(instance.id)} deleted',
            entity_type='Specialists',
            entity_id=instance.id,
            metadata={},
        )
        instance.delete()



