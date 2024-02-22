from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from rest_framework.request import Request

from sendables.core.serializers import SendSerializer
from sendables.core.utils import assert_all_requested_valid

User = get_user_model()


def get_valid_recipients_lenient(
    request: Request,
    requested_recipient_keys: list[str],
    send_serializer: SendSerializer,
    *args: Any,
    **kwargs: Any,
) -> QuerySet:
    """Lenient method of choosing valid recipients, out of a group of requested keys.

    Pick existent keys, possibly exclude current user, and quitely ignore the rest.

    Args:
        request: The request object
        requested_recipient_keys: Requested recipients' identifying keys
        send_serializer: The "send" action's serializer

    Returns:
        A QuerySet of eligible recipients
    """
    filters = {f"{send_serializer.item_key_name}__in": requested_recipient_keys}
    recipients = User.objects.filter(**filters)

    if callable(setting := send_serializer.entity_settings.ALLOW_SEND_TO_SELF):
        allow_send_to_self = setting(request)
    else:
        allow_send_to_self = setting

    if not allow_send_to_self:
        recipients = recipients.exclude(pk=request.user.pk)

    return recipients


def get_valid_recipients_strict(
    request: Request,
    requested_recipient_keys: list[str],
    send_serializer: SendSerializer,
    *args: Any,
    **kwargs: Any,
) -> QuerySet:
    """Strict method of choosing valid recipients, out of a group of requested keys.

    If given any non-existent keys, or possibly current user, respond with an error.

    Args:
        request: The request object
        requested_recipient_keys: Requested recipients' identifying keys
        send_serializer: The "send" action's serializer

    Returns:
        A QuerySet of eligible recipients

    Raises:
        ValidationError: On any invalid recipients found
    """
    recipients = get_valid_recipients_lenient(
        request, requested_recipient_keys, send_serializer
    )
    assert_all_requested_valid(requested_recipient_keys, recipients, send_serializer)

    return recipients
