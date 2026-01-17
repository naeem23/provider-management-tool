from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    UserReadSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsProviderAdmin, IsProviderAdminOrOwner
from .models import UserRole
from audit_log.models import AuditLog

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    Accounts API:
    - Provider Admin can create and manage users
    - Users can view themselves
    - List is limited to same provider (unless staff)
    """
    queryset = User.objects.select_related("provider").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserReadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # staff can see all
        if user.is_staff or user.is_superuser:
            return qs

        # provider isolation: see only your provider’s users
        if user.provider_id:
            if self.action == "list":
                return qs.filter(provider_id=user.provider_id).exclude(username=user.username)
            else:
                return qs.filter(provider_id=user.provider_id)

        # if user has no provider assigned, only themselves
        return qs.filter(id=user.id)

    def get_permissions(self):
        if self.action in ["create", "list"]:
            return [IsAuthenticated(), IsProviderAdmin()]

        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsProviderAdminOrOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = serializer.save()
        AuditLog.log_action(
            user=self.request.user,
            action_type='USER_CREATED',
            action_category='USER_MANAGEMENT',
            description=f'Create a new user with username: {user.username}',
            entity_type='User',
            entity_id=user.id,
            metadata={},
        )
    
    def perform_update(self, serializer):
        old_user = self.get_object()
        user = serializer.save()
        AuditLog.log_action(
            user=self.request.user,
            action_type='USER_UPDATED',
            action_category='USER_MANAGEMENT',
            description=f'User info updated for username: {user.username}',
            entity_type='User',
            entity_id=user.id,
            metadata={
                'old_data': {
                    'username': old_user.username,
                    'first_name': old_user.first_name,
                    'last_name': old_user.last_name,
                    'role': old_user.role,
                },
                'new_data':  {
                    'username': old_user.username,
                    'first_name': old_user.first_name,
                    'last_name': old_user.last_name,
                    'role': old_user.role,
                },
            },
        )
    
    def perform_destroy(self, instance):
        AuditLog.log_action(
            user=self.request.user,
            action_type='USER_DELETED',
            action_category='USER_MANAGEMENT',
            description=f'Username: {instance.username} deleted',
            entity_type='User',
            entity_id=instance.id,
            metadata={},
        )
        instance.delete()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = UserReadSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        AuditLog.log_action(
            user=request.user,
            action_type='USER_UPDATED',
            action_category='USER_MANAGEMENT',
            description=f'Password changed for user: {new_user.username}',
            entity_type='User',
            entity_id=user.id,
            metadata={},
        )

        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
