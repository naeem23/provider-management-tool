from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'message', 'is_read', 'entity_type', 'created_at']
    list_filter = ['is_read', 'entity_type']
    search_fields = ['title', 'message', 'entity_type',]
    ordering = ['-created_at']