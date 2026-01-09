from rest_framework import serializers
from django.utils import timezone

from .models import Contract, ContractVersion


class ContractReadSerializer(serializers.ModelSerializer):
    service_request_id = serializers.UUIDField(source="service_request.id", read_only=True)
    role_name = serializers.CharField(source="service_request.role_name", read_only=True)
    service_domain = serializers.CharField(source="service_request.domain", read_only=True)
    specialist_name = serializers.SerializerMethodField()
    expected_rate = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "contract_code",
            "title",
            "service_request_id",
            "role_name",
            "service_domain",
            "provider",
            "specialist_name",
            "offered_daily_rate",
            "negotiated_rate",
            "expected_rate",
            "status",
            "response_deadline",
            "days_left",
            "valid_from",
            "valid_to",
            "terms_and_condition",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "service_request_id",
            "created_at",
            "updated_at",
        ]

    def get_specialist_name(self, obj):
        if obj.winning_offer and obj.winning_offer.proposed_specialist:
            return obj.winning_offer.proposed_specialist.full_name
        return None

    def get_days_left(self, obj):
        if not obj.response_deadline:
            return None

        today = timezone.now().date()

        days = (obj.response_deadline - today).days
        return max(days, 0)

    def get_expected_rate(self, obj):
        if obj.winning_offer:
            return obj.winning_offer.daily_rate
        return None


class ContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ContractVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractVersion
        fields = "__all__"
        read_only_fields = [
            "id",
            "contract",
            "version_number",
            "created_at",
        ]