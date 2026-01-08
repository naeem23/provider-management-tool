from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

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
        if user.is_staff or user.is_superuser:
            return Specialist.objects.all()
        return Specialist.objects.filter(provider=user.provider)

    def perform_create(self, serializer):
        # Auto-assign provider based on logged-in user
        serializer.save(provider=self.request.user.provider)

