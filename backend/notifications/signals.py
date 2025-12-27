from django.db.models.signals import post_save
from django.dispatch import receiver

from audit_log.models import AuditLog
from .audit_mapping import handle_audit_event


@receiver(post_save, sender=AuditLog)
def create_notification_from_audit(sender, instance, created, **kwargs):
    if not created:
        return

    handle_audit_event(instance)
