from django.contrib import admin
from .models import Contract, ContractVersion


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['id', 'contract_code', 'status', 'valid_from', 'valid_till']
    list_filter = ['status',]
    search_fields = ['provider__provider_code', 'contract_code']
    ordering = ['-created_at']


@admin.register(ContractVersion)
class ContractVersionAdmin(admin.ModelAdmin):
    list_display = ['id', 'contract', 'version_number']
    search_fields = ['contract__contract_code',]
    ordering = ['-created_at']