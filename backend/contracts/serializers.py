from rest_framework import serializers

from .models import Contract, ContractVersion


class ContractReadSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="service_request.role_name", read_only=True)
    specialist_name = serializers.CharField(source="specialist.full_name", read_only=True)
    provider_name = serializers.CharField(source="specialist.provider.name", read_only=True)
    providers_expected_rate = serializers.SerializerMethodField()
    proposed_rate = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "contract_code",
            "service_request",
            "title",
            "role_name",
            "domain",
            "provider",
            "provider_name",
            "specialist",
            "specialist_name",
            "proposed_rate",
            "negotiated_rate",
            "providers_expected_rate",
            "status",
            "response_deadline",
            "valid_from",
            "valid_till",
            "terms_and_condition",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_specialist_name(self, obj):
        if obj.specialist:
            return specialist.full_name
        if obj.winning_offer and obj.winning_offer.proposed_specialist:
            return obj.winning_offer.proposed_specialist.full_name
        return None

    def get_providers_expected_rate(self, obj):
        return str(obj.providers_expected_rate)

    def get_proposed_rate(self, obj):
        latest_versions = obj.versions.order_by('-version_number').first()

        if latest_versions:
            return str(latest_versions.counter_rate)
        return str(obj.proposed_rate)


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


class StartNegotiationSerializer(serializers.Serializer):
    """
    Serializer for starting contract negotiation
    Validates incoming data from frontend/3rd party
    """
    id = serializers.CharField(required=True, help_text="External contract ID from 3rd party")
    title = serializers.CharField(required=True, max_length=255)
    proposed_rate = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    valid_from = serializers.DateField(required=True)
    valid_till = serializers.DateField(required=True)
    response_deadline = serializers.DateField(required=True)
    domain = serializers.CharField(required=False, allow_blank=True)
    terms_condition = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.CharField(required=False, allow_blank=True)


class CounterOfferSerializer(serializers.Serializer):
    """
    Serializer for submitting counter offer
    """
    counter_rate = serializers.DecimalField(
        required=True, 
        max_digits=10, 
        decimal_places=2,
        help_text="Proposed counter rate"
    )
    counter_explanation = serializers.CharField(
        required=True,
        min_length=10,
        help_text="Explanation for the counter offer"
    )
    counter_terms = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Terms and conditions for counter offer"
    )
    
    def validate_counter_rate(self, value):
        """Validate counter rate is positive"""
        if value <= 0:
            raise serializers.ValidationError("Counter rate must be positive")
        return value
    
    def validate_counter_explanation(self, value):
        """Validate explanation is meaningful"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Counter explanation must be at least 10 characters"
            )
        return value.strip()