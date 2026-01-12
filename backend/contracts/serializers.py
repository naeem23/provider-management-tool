from rest_framework import serializers

from .models import Contract, ContractVersion


class ContractReadSerializer(serializers.ModelSerializer):
    service_request_code = serializers.CharField(source="service_request.external_request_id", read_only=True)
    role_name = serializers.CharField(source="service_request.role_name", read_only=True)
    service_domain = serializers.CharField(source="service_request.domain", read_only=True)
    specialist_name = serializers.SerializerMethodField()
    expected_rate = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "contract_code",
            "service_request",
            "service_request_code",
            "title",
            "role_name",
            "service_domain",
            "provider",
            "specialist_name",
            "offered_daily_rate",
            "negotiated_rate",
            "expected_rate",
            "status",
            "response_deadline",
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