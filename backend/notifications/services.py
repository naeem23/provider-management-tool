from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


def notify_roles(*, role, title, message, entity_type, entity_id):
    users = User.objects.filter(role=role)

    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        for user in users
    ]
    Notification.objects.bulk_create(notifications)


def notify_user(*, user, title, message, entity_type, entity_id):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
    )
