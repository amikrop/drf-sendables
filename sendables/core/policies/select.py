from django.db.models import QuerySet
from rest_framework.request import Request

from sendables.core.serializers import SelectSerializer
from sendables.core.types import ManagedModel
from sendables.core.utils import assert_all_requested_valid


def get_valid_items_lenient(
    request: Request,
    requested_keys: list[str],
    select_serializer: SelectSerializer,
    item_type: type[ManagedModel],
    user_role: str,
    **removal_filters: bool,
) -> QuerySet:
    """Lenient method of choosing valid items (database records), out of a group of
    requested keys.

    Pick existent keys that belong to current user and quitely ignore the rest.

    Args:
        request: The request object
        requested_keys: Requested items' identifying keys
        select_serializer: The "select" action's serializer
        item_type: Requested items' model class
        user_role: Current user's relation to the items
        removal_filters: Possible "is removed" filters

    Returns:
        A QuerySet of eligible items
    """
    filters = {
        f"{select_serializer.item_key_name}__in": requested_keys,
        user_role: request.user,
        **removal_filters,
    }
    return item_type.objects.filter(**filters)


def get_valid_items_strict(
    request: Request,
    requested_keys: list[str],
    select_serializer: SelectSerializer,
    item_type: type[ManagedModel],
    user_role: str,
    **removal_filters: bool,
) -> QuerySet:
    """Strict method of choosing valid items (database records), out of a group of
    requested keys.

    If given any values other than existent keys belonging to current user, respond
    with an error.

    Args:
        request: The request object
        requested_keys: Requested items' identifying keys
        select_serializer: The "select" action's serializer
        item_type: Requested items' model class
        user_role: Current user's relation to the items
        removal_filters: Possible "is removed" filters

    Returns:
        A QuerySet of eligible items

    Raises:
        ValidationError: On any invalid items found
    """
    valid_items = get_valid_items_lenient(
        request,
        requested_keys,
        select_serializer,
        item_type,
        user_role,
        **removal_filters,
    )
    assert_all_requested_valid(requested_keys, valid_items, select_serializer)

    return valid_items
