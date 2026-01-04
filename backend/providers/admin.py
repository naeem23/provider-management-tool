from django.contrib import admin
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'provider_code', 'email', 'phone']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'provider_code', 'email', 'phone']
    ordering = ['-created_at']

