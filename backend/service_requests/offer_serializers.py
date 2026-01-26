from rest_framework import serializers
from .models import RequestStatus, ServiceOffer, OfferStatus, ServiceRequest


class ServiceOfferReadSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source="request.id", read_only=True)
    request_title = serializers.CharField(source="request.title", read_only=True)
    request_duration = serializers.SerializerMethodField()
    role_name = serializers.CharField(source="proposed_specialist.role_name", read_only=True)
    provider_id = serializers.UUIDField(source="provider.id", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    specialist_id = serializers.UUIDField(source="proposed_specialist.id", read_only=True)
    specialist_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOffer
        fields = [
            "id",
            "request_id",
            "request_title",
            "request_duration",
            "role_name",
            "provider_id",
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
            return obj.proposed_specialist.full_name
        return None

    def get_request_duration(self, obj):
        return f"{obj.request.start_date} to {obj.request.end_date}"


class ServiceOfferCreateSerializer(serializers.ModelSerializer):
    """
    Supplier creates a DRAFT offer.
    """

    class Meta:
        model = ServiceOffer
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'updated_at']
