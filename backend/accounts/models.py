from django.contrib.auth.models import AbstractUser
from django.db import models
from integrations.flowable_service import FlowableUserService
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
        on_delete=models.CASCADE,
        related_name="users"
    )

    def sync_to_flowable(self, groups=None):
        """Sync this user to Flowable"""
        try:
            # Create user in Flowable
            FlowableUserService.create_user(
                username=self.username,
                first_name=self.first_name,
                last_name=self.last_name,
                email=self.email,
                password=self.password
            )
            
            # Assign to groups
            FlowableUserService.add_user_to_group(self.username, self.role.lower())
            
            return True
        except Exception as e:
            print(f"Error syncing to Flowable: {e}")
            return False
    