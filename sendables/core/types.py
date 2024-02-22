import enum
from typing import TYPE_CHECKING, Any, Callable, Protocol

from django.db import models
from rest_framework import pagination, serializers


class FilterType(enum.Enum):
    """Search filter type, applied against model fields."""

    EQUALS = 0
    CONTAINS = 1
    DATETIME = 2


if TYPE_CHECKING:
    from sendables.core.settings import Settings

    class Configured:
        entity_settings: Settings
        get_view_setting: Callable[[str], Any]

    class GenericViewProtocol(Protocol):
        kwargs: dict[str, Any]

        def get_serializer_context(self) -> dict[str, Any]: ...

    class ManagedModel(models.Model):
        objects: models.Manager

    class SettingsBase:
        SENDABLE_CLASS: type[ManagedModel]
        LIST_SERIALIZER_CLASS: type[serializers.Serializer]
        LIST_SENT_SERIALIZER_CLASS: type[serializers.Serializer]
        DETAIL_SERIALIZER_CLASS: type[serializers.Serializer]
        DETAIL_SENT_SERIALIZER_CLASS: type[serializers.Serializer]
        GET_VALID_RECIPIENTS: Callable[..., models.QuerySet]
        SEND_SERIALIZER_CLASS: type[serializers.Serializer]
        SENT_FIELD_NAMES: list[str]
        PAGINATION_CLASS: type[pagination.BasePagination] | None

else:

    class Configured:
        pass

    class GenericViewProtocol:
        pass

    class ManagedModel:
        pass

    class SettingsBase:
        pass
