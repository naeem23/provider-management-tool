from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'actor', 'action', 'entity_type', 'created_at']
    list_filter = ['entity_type',]
    search_fields = ['actor__username', 'action', 'entity_type',]
    ordering = ['-created_at']