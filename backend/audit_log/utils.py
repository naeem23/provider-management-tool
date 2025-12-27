from .models import AuditLog, AuditAction
from .middleware import get_current_request


def log_audit_event(action, entity):
    request = get_current_request()
    user = request.user if request and request.user.is_authenticated else None

    AuditLog.objects.create(
        actor=user,
        actor_role=getattr(user, "role", ""),
        action=action,
        entity_type=entity.__class__.__name__,
        entity_id=str(entity.pk),
        after={"status": getattr(entity, "status", None)},
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        endpoint=request.path if request else "",
    )
