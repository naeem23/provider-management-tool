from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    UserReadSerializer,
    UserCreateSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsProviderAdmin
from .models import UserRole

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
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
        return UserReadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # staff can see all
        if user.is_staff or user.is_superuser:
            return qs

        # provider isolation: see only your provider’s users
        if user.provider_id:
            return qs.filter(provider_id=user.provider_id)

        # if user has no provider assigned, only themselves
        return qs.filter(id=user.id)

    def get_permissions(self):
        # Only Provider Admin can create/update users (except "me" actions)
        if self.action in ["create", "update", "partial_update"]:
            return [IsAuthenticated(), IsProviderAdmin()]
        return super().get_permissions()

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
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
