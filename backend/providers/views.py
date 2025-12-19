from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Provider
from .serializers import ProviderSerializer
from .permissions import IsProviderAdmin


class ProviderViewSet(viewsets.ModelViewSet):
    """
    CRUD API for managing Providers.
    Only Provider Admins can create or update.
    """
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated, IsProviderAdmin]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsAuthenticated(), IsProviderAdmin()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get"], url_path="specialists")
    def specialists(self, request, pk=None):
        """
        Get specialists of a particular provider.
        """
        provider = self.get_object()
        specialists = Specialist.objects.filter(provider=provider)
        serializer = SpecialistSerializer(specialists, many=True)
        return Response(serializer.data)

