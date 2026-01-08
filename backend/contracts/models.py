from django.db import models
import uuid


class ContractStatus(models.TextChoices):
    PENDING        = "PENDING", "Pending Approval"
    IN_NEGOTIATION = "IN_NEGOTIATION", "In Negotiation"
    ACTIVE         = "ACTIVE", "Active"
    EXPIRED        = "EXPIRED", "Expired"
    REJECTED       = "REJECTED", "Rejected"


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey("providers.Provider", on_delete=models.CASCADE, related_name="contracts")

    contract_code     = models.CharField(max_length=64, unique=True)
    status            = models.CharField(max_length=32, choices=ContractStatus.choices, default=ContractStatus.PENDING)

    valid_from        = models.DateField(null=True, blank=True)
    valid_to          = models.DateField(null=True, blank=True)

    functional_weight = models.PositiveSmallIntegerField(default=50)
    commercial_weight = models.PositiveSmallIntegerField(default=50)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)


class ContractVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="versions")

    version_number = models.PositiveIntegerField()
    payload        = models.JSONField(default=dict) # store terms/changes
    comment        = models.TextField(blank=True)

    created_by     = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("contract", "version_number")]


class PricingRule(models.Model):
    """
    Max price per (role, experience_level, technology_level).
    Can be attached to Contract; or to Provider if global rules.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="pricing_rules")

    role_name        = models.CharField(max_length=128)
    experience_level = models.CharField(max_length=16)
    technology_level = models.CharField(max_length=8)

    max_daily_rate   = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = [("contract", "role_name", "experience_level", "technology_level")]
