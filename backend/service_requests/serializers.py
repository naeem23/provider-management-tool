from rest_framework import serializers
from .models import ServiceRequest


class ServiceRequestReadSerializer(serializers.ModelSerializer):
    offers_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "external_request_id",
            "status",
            "domain",
            "role_name",
            "technology",
            "experience_level",
            "technology_level",
            "start_date",
            "end_date",
            "expected_man_days",
            "criteria_json",
            "offers_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
            "offers_count",
        ]


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """
    Used when requests are imported or manually created.
    """

    class Meta:
        model = ServiceRequest
        fields = [
            "external_request_id",
            "domain",
            "role_name",
            "technology",
            "experience_level",
            "technology_level",
            "start_date",
            "end_date",
            "expected_man_days",
            "criteria_json",
        ]


class ServiceRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Only editable fields before request is OPEN.
    """

    class Meta:
        model = ServiceRequest
        fields = [
            "domain",
            "role_name",
            "technology",
            "experience_level",
            "technology_level",
            "start_date",
            "end_date",
            "expected_man_days",
            "criteria_json",
        ]
