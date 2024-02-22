import inspect
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, cast

import django
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.db.models import Model, Q, QuerySet
from django.db.models.base import ModelBase
from rest_framework import serializers
from rest_framework.serializers import IntegerField, UUIDField

from sendables.core.settings import POSSIBLY_CONCRETE_MODELS, Settings
from sendables.core.types import FilterType

if TYPE_CHECKING:
    from sendables.core.serializers import ContainerSerializer


def conditionally_concrete(model_class: type[Model]) -> type[Model]:
    """Add given model class to the set of candidates to become concrete Django models,
    if found to be directly used as sendable entity types.
    """
    POSSIBLY_CONCRETE_MODELS.add(model_class)
    return model_class


def check_direct_model_usage(entity_settings: Settings) -> None:
    """If sendable entity type used by given settings is in the candidates set and not
    already concrete, define a new concrete model with the same fields and set it back
    as the settings entry. Also update the name in its module to now hold the new model.
    """
    if not (
        (model_class := entity_settings.SENDABLE_CLASS) in POSSIBLY_CONCRETE_MODELS
        and model_class._meta.abstract
    ):
        return

    # Copy required model attributes
    fields = {field.name: field for field in model_class._meta.fields}
    module_name = model_class.__dict__["__module__"]
    attrs = {"__module__": module_name, **fields}

    # Generate concrete model class
    concrete_model_class = ModelBase(model_class.__name__, (model_class,), attrs)

    # Set it to settings
    entity_settings.SENDABLE_CLASS = concrete_model_class  # type: ignore[assignment]

    # Set it to original model's module
    module = inspect.getmodule(model_class)
    setattr(module, model_class.__name__, concrete_model_class)


def get_url_arg_type(serializer_field_type: type[serializers.Field]) -> str:
    """Get URL argument type out of serializer field type."""
    type_mapping = {
        IntegerField: "int",
        UUIDField: "uuid",
    }
    return type_mapping.get(serializer_field_type, "str")


def assert_all_requested_valid(
    requested_item_keys: list[str],
    valid_items: QuerySet,
    serializer: "ContainerSerializer",
) -> None:
    """Require the validity of all given items.

    Respond with error if any of the requested item keys does not have a matching valid
    item, indicating those which fail the check.

    Args:
        requested_item_keys: Requested items' identifying keys
        valid_items: The valid items
        serializer: The action's serializer

    Raises:
        ValidationError: On any invalid items found
    """
    key_name = serializer.item_key_name
    valid_item_keys = set(getattr(item, key_name) for item in valid_items)

    invalid_item_keys = sorted(set(requested_item_keys) - valid_item_keys)

    if invalid_item_keys:
        invalid_items_display = ", ".join(map(str, invalid_item_keys))
        error_message = (
            f"Invalid {serializer.item_entity_name}s: {invalid_items_display}."
        )
        raise serializers.ValidationError({serializer.items_field_name: error_message})


def filter_queryset(
    query_params: dict[str, list[str]],
    queryset: QuerySet,
    filter_type_mapping: dict[str, FilterType],
) -> QuerySet:
    """Filter given QuerySet based on grouped query parameters.

    Filter groups of different field keys are joined with an "AND" between them, while
    filters of the same key are joined with an "OR".

    "Equals" and "contains" filters must be present as-is in the filter type mapping.
    "Datetime" filters support double underscore querying.

    Args:
        query_params: Mapping of query parameter name to a list of its values
        queryset: The QuerySet to be filtered
        filter_type_mapping: Mapping of query parameter names to filter types

    Returns:
        The filtered QuerySet
    """
    filter_type: FilterType | None
    filter_dict: dict[str, Any]
    filters = Q()

    for filter_key, filter_values in query_params.items():
        try:
            filter_type = filter_type_mapping[filter_key]
        except KeyError:
            # Try to get a "datetime" filter.
            field_key = filter_key.split("__")[0]
            field_filter_type = filter_type_mapping.get(field_key)
            if (filter_type := field_filter_type) != FilterType.DATETIME:
                continue

        # New filter group, joined with "AND" with the other groups.
        filter_group = Q()
        for value in filter_values:
            if filter_type == FilterType.EQUALS:
                filter_dict = {filter_key: value}
            elif filter_type == FilterType.CONTAINS:
                filter_dict = {filter_key + "__icontains": value}
            else:
                kwargs = {}
                if django.VERSION >= (5, 0) or settings.USE_TZ:
                    kwargs = {"tz": timezone.utc}

                try:
                    datetime_object = datetime.fromtimestamp(float(value), **kwargs)
                except ValueError:
                    continue

                filter_dict = {filter_key: datetime_object}

            # Different value of same filter key, joined with "OR" with the rest
            # of the group.
            filter_group |= Q(**filter_dict)

        filters &= filter_group

    try:
        return queryset.filter(filters)
    except (FieldError, ValidationError):
        return cast(QuerySet, queryset.model.objects.none())
