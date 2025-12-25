from rest_framework import serializers
from .models import Contract, ContractVersion, PricingRule


class ContractReadSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "contract_code",
            "provider",
            "provider_name",
            "status",
            "valid_from",
            "valid_to",
            "functional_weight",
            "commercial_weight",
            "created_at",
            "updated_at",
        ]


class ContractCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            "contract_code",
            "provider",
            "valid_from",
            "valid_to",
            "functional_weight",
            "commercial_weight",
        ]


class ContractVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = ContractVersion
        fields = [
            "id",
            "contract",
            "version_number",
            "payload",
            "comment",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = [
            "version_number",
            "created_by",
            "created_at",
        ]


class PricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingRule
        fields = [
            "id",
            "contract",
            "role_name",
            "experience_level",
            "technology_level",
            "max_daily_rate",
        ]
