from rest_framework import serializers
from .models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ["id", "name", "provider_code", "email", "phone", "address_line1", 
                  "address_line2", "city", "postal_code", "country", "is_active", 
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


