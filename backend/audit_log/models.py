from django.db import models
import uuid


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actor       = models.ForeignKey(
        "accounts.User", 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )
    actor_role  = models.CharField(max_length=32, blank=True)
    action      = models.CharField(max_length=32, choices=AuditAction.choices)
    entity_type = models.CharField(max_length=64)  # e.g. ServiceRequest
    entity_id   = models.CharField(max_length=64)  # store UUID as string

    before      = models.JSONField(null=True, blank=True)
    after       = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    endpoint = models.CharField(max_length=255, blank=True, null=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["actor"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]