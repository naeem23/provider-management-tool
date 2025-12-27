from .models import Notification


def create_notification(
    *,
    user,
    title,
    message,
    entity=None,
):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        entity_type=entity.__class__.__name__ if entity else "",
        entity_id=str(entity.pk) if entity else "",
    )
