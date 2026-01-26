from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from accounts.models import User, UserRole
from .models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = "__all__"
        read_only_fields = ("id", "provider_code", "created_at", "updated_at")


class ProviderAdminRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3)
    password = serializers.CharField(min_length=6, write_only=True)
    provider_id = serializers.UUIDField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_provider_id(self, value):
        try:
            provider = Provider.objects.get(id=value)
        except Provider.DoesNotExist:
            raise serializers.ValidationError("Invalid provider ID.")

        if User.objects.filter(provider=provider,role=UserRole.PROVIDER_ADMIN).exists():
            raise serializers.ValidationError(
                "Provider admin already exists for this provider."
            )

        return value

    def validate_password(self, value):
        """
        Validate password using Django's built-in validators
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    @transaction.atomic
    def create(self, validated_data):
        provider = Provider.objects.get(id=validated_data["provider_id"])

        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            role=UserRole.PROVIDER_ADMIN,
            provider=provider,
            is_staff=True,
            is_active=True,
        )

        return user