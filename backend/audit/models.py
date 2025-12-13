from django.db import models
import uuid


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actor       = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    entity_type = models.CharField(max_length=64)  # e.g. "Provider"
    entity_id   = models.CharField(max_length=64)  # store UUID as string
    action      = models.CharField(max_length=32)  # CREATE/UPDATE/DELETE

    before      = models.JSONField(null=True, blank=True)
    after       = models.JSONField(null=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
