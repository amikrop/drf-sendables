from django.db.models import QuerySet
from rest_framework.request import Request

from sendables.core.settings import Settings
from sendables.core.utils import filter_queryset


def filter_sendables(
    request: Request, sendables: QuerySet, entity_settings: Settings
) -> QuerySet:
    """Filter given sendables, using their respective URL query parameters.

    Args:
        request: The request object
        sendables: The sendables QuerySet to be filtered
        entity_settings: The Settings object for current entity

    Returns:
        The filtered sendables QuerySet
    """
    # Keep only query parameters whose name does not start with "recipient_".
    query_params_sendables = {
        key: request.query_params.getlist(key)
        for key in request.query_params
        if not key.startswith("recipient_")
    }
    return filter_queryset(
        query_params_sendables, sendables, entity_settings.FILTER_FIELDS_SENDABLES
    )


def filter_recipients(
    request: Request, users: QuerySet, entity_settings: Settings
) -> QuerySet:
    """Filter given recipients, using their respective URL query parameters.

    Args:
        request: The request object
        users: The users QuerySet to be filtered
        entity_settings: The Settings object for current entity

    Returns:
        The filtered users QuerySet
    """
    # Keep only query parameters whose name starts with "recipient_". Pass them down
    # without that prefix.
    query_params_recipients = {
        key[10:]: request.query_params.getlist(key)
        for key in request.query_params
        if key.startswith("recipient_")
    }
    return filter_queryset(
        query_params_recipients, users, entity_settings.FILTER_FIELDS_RECIPIENTS
    )
