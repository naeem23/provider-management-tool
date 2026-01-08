from rest_framework import serializers
from .models import Specialist


class SpecialistSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Specialist
        fields = '__all__'
        read_only_fields = ["id", "specialist_code", "created_at", "updated_at", "provider"]