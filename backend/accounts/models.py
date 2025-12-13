from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class UserRole(models.TextChoices):
    PROVIDER_ADMIN       = "PROVIDER_ADMIN", "Provider Admin"
    SUPPLIER_REP         = "SUPPLIER_REP", "Supplier Representative"
    CONTRACT_COORDINATOR = "CONTRACT_COORDINATOR", "Contract Coordinator"
    INTERNAL_PM          = "INTERNAL_PM", "Internal Project Manager" #optional


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=32, choices=UserRole.choices)
    provider = models.ForeignKey(
        "providers.Provider",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="users"
    )