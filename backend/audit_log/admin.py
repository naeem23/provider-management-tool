from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action_type', 'entity_type', 'created_at']
    list_filter = ['entity_type',]
    search_fields = ['user__username', 'action_type', 'entity_type',]
    ordering = ['-created_at']