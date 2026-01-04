from django.contrib import admin
from .models import Specialist


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider', 'first_name', 'last_name', 'role_name']
    list_filter = ['role_name', 'experience_level', 'technology_level', 'avg_daily_rate', 'performance_grade', 'is_available']
    search_fields = ['first_name', 'last_name', 'role_name']
    ordering = ['-created_at']

