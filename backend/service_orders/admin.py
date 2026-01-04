from django.contrib import admin
from .models import ServiceOrder


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'provider', 'status', 'start_date', 'end_date']
    list_filter = ['status',]
    search_fields = ['request__id', 'provider__id', 'start_date', 'end_date']
    ordering = ['-created_at']