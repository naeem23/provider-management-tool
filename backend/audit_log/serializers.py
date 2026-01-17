from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import AuditLog

User = get_user_model()

class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )

    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = ['created_at',]
