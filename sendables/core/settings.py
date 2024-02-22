from typing import Any

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from sendables.core.types import FilterType, SettingsBase

POSSIBLY_CONCRETE_MODELS: set[type[models.Model]] = set()

DEFAULTS = {
    # Sending
    "SEND_SERIALIZER_CLASS": "sendables.core.serializers.SendSerializer",
    "ALLOW_SEND_TO_SELF": False,
    "SENT_FIELD_NAMES": ["content"],
    # Senders/recipients
    "PARTICIPANT_KEY_NAME": "id",
    "PARTICIPANT_KEY_TYPE": "rest_framework.serializers.IntegerField",
    "GET_VALID_RECIPIENTS": "sendables.core.policies.send.get_valid_recipients_lenient",
    # Sendables
    "SENDABLE_CLASS": "sendables.core.models.Sendable",
    "SENDABLE_KEY_NAME": "id",
    "SENDABLE_KEY_TYPE": "rest_framework.serializers.IntegerField",
    "GET_VALID_ITEMS": "sendables.core.policies.select.get_valid_items_lenient",
    "LIST_SERIALIZER_CLASS": "sendables.core.serializers.ReceivedSendableSerializer",
    "DETAIL_SERIALIZER_CLASS": "sendables.core.serializers.ReceivedSendableSerializer",
    # Ordering
    "SORT_RECEIVED_KEY": "sendables.core.policies.list.sort_received_key",
    "SORT_SENT_KEY": "sendables.core.policies.list.sort_sent_key",
    # Filter functions
    "FILTER_SENDABLES": "sendables.core.policies.filter.filter_sendables",
    "FILTER_RECIPIENTS": "sendables.core.policies.filter.filter_recipients",
    # Filter fields with their types
    "FILTER_FIELDS_SENDABLES": {
        "content": FilterType.CONTAINS,
        "sent_on": FilterType.DATETIME,
        "sender__id": FilterType.EQUALS,
        "sender__username": FilterType.EQUALS,
    },
    "FILTER_FIELDS_RECIPIENTS": {
        "id": FilterType.EQUALS,
        "username": FilterType.EQUALS,
    },
    # Misc
    "AFTER_SEND_CALLBACKS": [],
    "DELETE_HANGING_SENDABLES": True,
    "GET_RECEIVED_PREFETCH_FIELDS": (
        "sendables.core.policies.list.get_received_prefetch_fields"
    ),
    "PAGINATION_CLASS": None,
}

IMPORT_STRINGS = {
    "SEND_SERIALIZER_CLASS",
    "ALLOW_SEND_TO_SELF",
    "PARTICIPANT_KEY_TYPE",
    "GET_VALID_RECIPIENTS",
    "SENDABLE_CLASS",
    "SENDABLE_KEY_TYPE",
    "GET_VALID_ITEMS",
    "LIST_SERIALIZER_CLASS",
    "DETAIL_SERIALIZER_CLASS",
    "SORT_RECEIVED_KEY",
    "SORT_SENT_KEY",
    "FILTER_SENDABLES",
    "FILTER_RECIPIENTS",
    "AFTER_SEND_CALLBACKS",
    "GET_RECEIVED_PREFETCH_FIELDS",
    "PAGINATION_CLASS",
}

PERMISSION_TYPES = [
    "SEND",
    "MARK_AS_READ",
    "MARK_AS_UNREAD",
    "DELETE",
    "DELETE_SENT",
    "LIST",
    "LIST_READ",
    "LIST_UNREAD",
    "LIST_SENT",
    "DETAIL",
    "DETAIL_SENT",
]

for permission_type in PERMISSION_TYPES:
    permission_key = permission_type + "_PERMISSIONS"

    DEFAULTS[permission_key] = ["rest_framework.permissions.IsAuthenticated"]
    IMPORT_STRINGS.add(permission_key)

LIST_TYPES = [
    "LIST",
    "LIST_READ",
    "LIST_UNREAD",
    "LIST_SENT",
]

for setting_name in ["_FILTER_SENDABLES", "_PAGINATION_CLASS"]:
    for list_type in LIST_TYPES:
        setting_key = list_type + setting_name

        DEFAULTS[setting_key] = None
        IMPORT_STRINGS.add(setting_key)


def _as_object(value: Any) -> Any:
    if isinstance(value, str):
        return import_string(value)

    return value


def _maybe_import(key: str, value: Any) -> Any:
    if key in IMPORT_STRINGS:
        if isinstance(value, (list, tuple)):
            value = [_as_object(item) for item in value]
        else:
            value = _as_object(value)

    return value


class Settings(SettingsBase):
    """Per entity-type settings.

    Priority:
        1. Global/project user settings
        2. Entity type defaults
        3. App defaults
    """

    def __init__(self, key: str, defaults: dict[str, Any]) -> None:
        self.key = key
        self.defaults = defaults

    def __getattr__(self, name: str) -> Any:
        try:
            # Global/project user setting
            value = settings.SENDABLES[self.key][name]  # type: ignore[misc]
        except (AttributeError, KeyError):
            try:
                # Entity type default
                value = self.defaults[name]
            except KeyError:
                # App default
                value = DEFAULTS[name]

        value = _maybe_import(name, value)

        setattr(self, name, value)
        return value


class AppSettings(dict[str, Settings]):
    """Container for settings of all of the app's entity types."""

    def __setitem__(self, key: str, value: Any) -> None:
        settings_object = Settings(key, value)
        super().__setitem__(key, settings_object)

    def __getitem__(self, key: str) -> Settings:
        # Implement `__getitem__` instead of subclassing `collections.defaultdict`, to
        # get the customly constructed value even on the first failed access attempt.
        try:
            return super().__getitem__(key)
        except KeyError:
            self[key] = {}
            return super().__getitem__(key)


app_settings = AppSettings()
