import uuid
from django.db import models


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        "accounts.User", 
        on_delete=models.CASCADE, 
        related_name="notifications"
    )

    title       = models.CharField(max_length=255)
    message     = models.TextField()

    is_read     = models.BooleanField(default=False)

    # optional: link a notification to a business entity
    entity_type = models.CharField(max_length=64, blank=True) # e.g. "ServiceRequest"
    entity_id   = models.CharField(max_length=64, blank=True) # UUID as string

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]