from rest_framework import serializers
from .models import ServiceOffer, OfferStatus, ServiceRequest


class ServiceOfferReadSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source="request.id", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    specialist_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceOffer
        fields = [
            "id",
            "request_id",
            "provider",
            "provider_name",
            "proposed_specialist",
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
            "status",
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
        fields = [
            "request",
            "proposed_specialist",
            "daily_rate",
            "travel_cost",
            "total_cost",
            "notes",
        ]

    def validate(self, data):
        request = data["request"]

        if request.status != request.status.OPEN:
            raise serializers.ValidationError("Offers can only be created for OPEN requests.")

        return data


class ServiceOfferUpdateSerializer(serializers.ModelSerializer):
    """
    Draft offers can be edited before submission.
    """

    class Meta:
        model = ServiceOffer
        fields = [
            "proposed_specialist",
            "daily_rate",
            "travel_cost",
            "total_cost",
            "notes",
        ]
