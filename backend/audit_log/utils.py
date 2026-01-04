from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

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


def serialize_for_json(data):
    """
    Recursively convert non-JSON-serializable objects
    (datetime, date, Decimal, UUID) into safe values.
    """
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}

    if isinstance(data, list):
        return [serialize_for_json(v) for v in data]

    if isinstance(data, UUID):
        return str(data)

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    return data
