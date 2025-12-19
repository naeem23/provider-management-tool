from rest_framework import serializers
from .models import Specialist


class SpecialistSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Specialist
        fields = ["id", "first_name", "last_name", "role_name", "experience_level", 
                  "technology_level", "avg_daily_rate", "performance_grade", 
                  "is_available", "provider_name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]