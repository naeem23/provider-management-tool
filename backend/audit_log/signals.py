import sys
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict

from .models import AuditLog, AuditAction
from .middleware import get_current_request
from .utils import serialize_for_json


def _get_actor_data():
    request = get_current_request()
    if not request or not hasattr(request, "user"):
        return None, None, None, None

    user = request.user if request.user.is_authenticated else None
    return (
        user,
        getattr(user, "role", ""),
        request.META.get("REMOTE_ADDR"),
        request.path if request else "",
    )


@receiver(pre_save)
def log_before_update(sender, instance, **kwargs):
    if is_running_migrations():
        return

    if not instance.pk:
        return

    try:
        old = sender.objects.get(pk=instance.pk)
        instance._audit_before = serialize_for_json(
            model_to_dict(
                old,
                exclude=["groups", "user_permissions"]
            )
        )
    except Exception:
        instance._audit_before = None


@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    # Avoid logging AuditLog itself
    if sender == AuditLog or is_running_migrations():
        return

    user, role, ip, endpoint = _get_actor_data()

    action = AuditAction.CREATE if created else AuditAction.UPDATE

    AuditLog.objects.create(
        actor=user,
        actor_role=role or "",
        action=action,
        entity_type=sender.__name__,
        entity_id=str(instance.pk),
        before=getattr(instance, "_audit_before", None),
        after=serialize_for_json(
            model_to_dict(
                instance,
                exclude=["groups", "user_permissions"]
            )
        ),
        ip_address=ip,
        endpoint=endpoint,
    )


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender == AuditLog or is_running_migrations():
        return

    user, role, ip, endpoint = _get_actor_data()

    AuditLog.objects.create(
        actor=user,
        actor_role=role or "",
        action=AuditAction.DELETE,
        entity_type=sender.__name__,
        entity_id=str(instance.pk),
        # before=serialize_for_json(model_to_dict(instance)),
        before=serialize_for_json(
            model_to_dict(
                instance,
                exclude=["groups", "user_permissions"]
            )
        ),
        after=None,
        ip_address=ip,
        endpoint=endpoint,
    )



def is_running_migrations():
    return "migrate" in sys.argv or "makemigrations" in sys.argv
