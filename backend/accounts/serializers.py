from django.contrib.auth import get_user_model
from rest_framework import serializers
from providers.models import Provider

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(source="provider.id", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
            "provider_id",
            "provider_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Use this for Provider Admin to create users.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    provider_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
            "password",
            "provider_id",
        ]
        read_only_fields = ["id"]
    
    def validate_provider_id(self, value):
        try:
            return Provider.objects.get(id=value)
        except Provider.DoesNotExist:
            raise serializers.ValidationError("Invalid provider ID")

    def create(self, validated_data):
        password = validated_data.pop("password")
        provider = validated_data.pop("provider_id")

        user = User(**validated_data, provider=provider)
        user.set_password(password)
        user.save()
        if user.role in ["SUPPLIER_REP", "CONTRACT_COORDINATOR"]:
            user.sync_to_flowable()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "password",
            "role",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        # Update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle password correctly
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
