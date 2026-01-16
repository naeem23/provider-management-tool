from rest_framework import serializers
from .models import RequestStatus, ServiceOffer, OfferStatus, ServiceRequest


class ServiceOfferReadSerializer(serializers.ModelSerializer):
    service_request_id = serializers.UUIDField(source="request.id", read_only=True)
    service_request_code = serializers.CharField(source="request.external_id", read_only=True)
    role_name = serializers.CharField(source="request.role_name", read_only=True)
    provider_id = serializers.UUIDField(source="provider.id", read_only=True)
    provider_code = serializers.CharField(source="provider.provider_code", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    specialist_id = serializers.UUIDField(source="proposed_specialist.id", read_only=True)
    specialist_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOffer
        fields = [
            "id",
            "service_request_id",
            "service_request_code",
            "role_name",
            "provider_id",
            "provider_code",
            "provider_name",
            "specialist_id",
            "specialist_name",
            "status",
            "daily_rate",
            "travel_cost",
            "total_cost",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_specialist_name(self, obj):
        if obj.proposed_specialist:
            return f"{obj.proposed_specialist.first_name} {obj.proposed_specialist.last_name}"
        return None


class ServiceOfferCreateSerializer(serializers.ModelSerializer):
    """
    Supplier creates a DRAFT offer.
    """

    class Meta:
        model = ServiceOffer
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'updated_at']
