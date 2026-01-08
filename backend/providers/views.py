from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import Provider
from .serializers import ProviderSerializer, ProviderAdminRegistrationSerializer
from .permissions import IsProviderAdmin
from specialists.models import Specialist
from audit_log.models import AuditLog

User = get_user_model()

class ProviderViewSet(viewsets.ModelViewSet):
    """
    CRUD API for managing Providers.
    Only Provider Admins can create or update.
    """
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer

    def get_permissions(self):
        if self.action in ["create", "create_provider_admin"]:
            return [AllowAny()]

        if self.action in ["update", "partial_update", "destroy", "metrics"]:
            return [IsAuthenticated(), IsProviderAdmin()]

        return [IsAuthenticated()]

    
    @action(detail=False, methods=["post"], url_path="register-admin", permission_classes=[AllowAny],)
    def create_provider_admin(self, request):
        serializer = ProviderAdminRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "role": user.role,
                    "provider_id": str(user.provider.id),
                },
            },
            status=status.HTTP_201_CREATED,
        )


    @action(detail=True, methods=["get"], url_path="specialists")
    def specialists(self, request, pk=None):
        """
        Get specialists of a particular provider.
        """
        provider = self.get_object()
        specialists = Specialist.objects.filter(provider=provider)
        serializer = SpecialistSerializer(specialists, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'], url_path='metrics')
    def metrics(self, request):
        """
        Get dashboard metrics for provider admin.
        Returns counts of users, specialist, and activity.
        """
        total_users = User.objects.filter(
            provider=request.user.provider
        ).count()

        total_specialists = Specialist.objects.filter(
            provider=request.user.provider
        ).count()

        active_specialist = Specialist.objects.filter(
            provider=request.user.provider,
            status="Active"
        ).count()

        # recent_activity = AuditLog.objects.filter(

        # )
        
        metrics_data = {
            "total_users": total_users,
            "total_specialists": total_specialists,
            "active_specialist": active_specialist
        }
        
        return Response(metrics_data, status=status.HTTP_200_OK)