from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import Specialist
from .serializers import SpecialistSerializer
from providers.permissions import IsProviderAdmin


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
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        queryset = self.queryset

        if user.is_staff or user.is_superuser:
            return queryset

        
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
            return queryset

        return queryset.filter(provider=user.provider)

    def perform_create(self, serializer):
        # Auto-assign provider based on logged-in user
        serializer.save(provider=self.request.user.provider)

