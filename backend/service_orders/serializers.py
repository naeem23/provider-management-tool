from rest_framework import serializers
from .models import (
    ServiceOrder,
    SubstitutionRequest,
    ExtensionRequest,
    OrderStatus,
)


class ServiceOrderReadSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    specialist_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOrder
        fields = [
            "id",
            "provider",
            "provider_name",
            "specialist",
            "specialist_name",
            "status",
            "start_date",
            "end_date",
            "man_days",
            "created_at",
            "updated_at",
        ]

    def get_specialist_name(self, obj):
        if obj.specialist:
            return f"{obj.specialist.first_name} {obj.specialist.last_name}"
        return None


class ServiceOrderCreateSerializer(serializers.ModelSerializer):
    """
    Created from accepted ServiceOffer.
    """

    class Meta:
        model = ServiceOrder
        fields = [
            "request",
            "winning_offer",
            "provider",
            "specialist",
            "start_date",
            "end_date",
            "man_days",
        ]


class SubstitutionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubstitutionRequest
        fields = [
            "id",
            "order",
            "current_specialist",
            "proposed_specialist",
            "reason",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]


class ExtensionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtensionRequest
        fields = [
            "id",
            "order",
            "new_end_date",
            "additional_man_days",
            "reason",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]
