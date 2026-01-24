from django.db import models
from django.core.validators import MinValueValidator
import uuid


class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('SUSPENDED', 'Suspended'),
        ('PENDING_EXTENSION', 'Pending Extension'),
        ('PENDING_SUBSTITUTION', 'Pending Substitution'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    service_request_id = models.CharField(max_length=64)
    winning_offer_id = models.CharField(max_length=64)
    contract_id = models.CharField(max_length=64)

    title = models.CharField(max_length=255)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="ACTIVE")

    start_date = models.DateField(null=True, blank=True)
    original_end_date = models.DateField(null=True, blank=True)
    current_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    supplier_id = models.CharField(max_length=64)
    supplier_name = models.CharField(max_length=255)
    
    current_specialist_id = models.CharField(max_length=50)
    current_specialist_name = models.CharField(max_length=255)
    original_specialist_id = models.CharField(max_length=50)
    original_specialist_name = models.CharField(max_length=255)
    
    role = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    
    original_man_days = models.IntegerField(validators=[MinValueValidator(1)])
    current_man_days = models.IntegerField(validators=[MinValueValidator(1)])
    consumed_man_days = momodels.IntegerField(default=0)
    
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    original_contract_value = models.DecimalField(max_digits=10, decimal_places=2)
    current_contract_value = models.DecimalField(max_digits=10, decimal_places=2)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service_order_id} - {self.title}"
    
    @property
    def is_active(self):
        return self.status == 'ACTIVE'
    
    @property
    def remaining_man_days(self):
        return self.current_man_days - self.consumed_man_days
    
    @property
    def has_been_extended(self):
        return self.current_end_date > self.original_end_date
    
    @property
    def has_been_substituted(self):
        return self.current_specialist_id != self.original_specialist_id
    
    def can_request_extension(self):
        # return self.status == 'ACTIVE' and self.remaining_man_days < 20
        return self.status == 'ACTIVE'
    
    def can_request_substitution(self):
        return self.status in ['ACTIVE', 'PENDING_SUBSTITUTION']


class ChangeRequestStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Requested"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class SubstitutionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="substitutions")

    requested_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=ChangeRequestStatus.choices, default=ChangeRequestStatus.REQUESTED)

    current_specialist = models.ForeignKey("specialists.Specialist", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    proposed_specialist = models.ForeignKey("specialists.Specialist", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ExtensionRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name="extensions")

    requested_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=ChangeRequestStatus.choices, default=ChangeRequestStatus.REQUESTED)

    new_end_date = models.DateField(null=True, blank=True)
    additional_man_days = models.PositiveIntegerField(null=True, blank=True)

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
