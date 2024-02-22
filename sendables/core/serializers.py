import copy
from typing import Any, Callable

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from rest_framework import serializers

from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from sendables.core.settings import app_settings
from sendables.core.types import ManagedModel


class ReceivedSendableSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    is_read = serializers.BooleanField()
    content = serializers.CharField(source="sendable.content")
    sent_on = serializers.DateTimeField(source="sendable.sent_on")


class ContainerSerializer(serializers.Serializer):
    """Contains a `ListField` of certain-typed items."""

    item_entity_name: str
    item_type: type[ManagedModel] | None = None
    user_role: str = ""
    item_key_name: str
    item_key_type: Callable[[], serializers.Field]
    removal_filters: dict[str, bool] = {}
    get_valid_items: Callable[..., QuerySet]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.entity_name = self.context["entity_name"]
        self.entity_settings = app_settings[self.entity_name]

    @property
    def items_field_name(self) -> str:
        """Exposed name of the `ListField`."""
        return f"{self.item_entity_name}_{self.item_key_name}s"

    def get_fields(self) -> dict[str, serializers.Field]:
        fields = super().get_fields()

        fields[self.items_field_name] = serializers.ListField(
            child=self.item_key_type(), allow_empty=False
        )
        return fields

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Keep only valid items. Fail if there are none."""
        self.valid_items = self.get_valid_items(
            self.context["request"],
            data[self.items_field_name],
            self,
            self.item_type,
            self.user_role,
            **self.removal_filters,
        )
        if not self.valid_items:
            raise serializers.ValidationError(
                {self.items_field_name: f"No valid {self.item_entity_name}s."}
            )

        data[self.items_field_name] = [
            getattr(item, self.item_key_name) for item in self.valid_items
        ]
        return data


class SendSerializer(ContainerSerializer):
    """Creates and dispatches sendables to recipients."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        settings = self.entity_settings

        self.item_entity_name = "recipient"
        self.item_key_name = settings.PARTICIPANT_KEY_NAME
        self.item_key_type = settings.PARTICIPANT_KEY_TYPE
        self.get_valid_items = settings.GET_VALID_RECIPIENTS

    def get_fields(self) -> dict[str, serializers.Field]:
        """Dynamically add any desired fields from the detail serializer."""
        fields = super().get_fields()

        # Make a detail serializer instance and copy desired fields.
        detail_serializer = self.entity_settings.DETAIL_SERIALIZER_CLASS(
            context=self.context
        )
        for field_name in self.entity_settings.SENT_FIELD_NAMES:
            fields[field_name] = copy.deepcopy(detail_serializer[field_name]._field)

        return fields

    def save(self, **kwargs: Any) -> None:
        """Create new sendable data and invoke any post-send callbacks.

        Store the following:
        1. The sendable itself (content and anything else)
        2. Per-recipient references (users' inbox "copies")
        3. Sendable-recipient associations ("sent to who" info)
        """
        sent_fields = {
            field_name: self.validated_data["sendable"][field_name]
            for field_name in self.entity_settings.SENT_FIELD_NAMES
        }

        Sendable = self.entity_settings.SENDABLE_CLASS
        sendable = Sendable(**sent_fields, **kwargs)
        sendable.save()

        sent_copies = [
            ReceivedSendable(recipient=user, sendable=sendable)
            for user in self.valid_items
        ]
        ReceivedSendable.objects.bulk_create(sent_copies)

        associations = [
            RecipientSendableAssociation(recipient=user, sendable=sendable)
            for user in self.valid_items
        ]
        RecipientSendableAssociation.objects.bulk_create(associations)

        for callback in self.entity_settings.AFTER_SEND_CALLBACKS:
            callback(self.context["request"], sent_fields, self.valid_items)


class SelectSerializer(ContainerSerializer):
    """Contains selected received sendable references."""

    item_type: type[ManagedModel] = ReceivedSendable
    user_role = "recipient"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        settings = self.entity_settings

        self.item_entity_name = self.entity_name
        self.item_key_name = settings.SENDABLE_KEY_NAME
        self.item_key_type = settings.SENDABLE_KEY_TYPE
        self.get_valid_items = settings.GET_VALID_ITEMS


class MarkSerializer(SelectSerializer):
    """Marks selected received sendables as read/unread."""

    def mark(self, is_read: bool) -> None:
        self.valid_items.update(is_read=is_read)


class DeleteSerializer(SelectSerializer):
    """Deletes selected received sendables."""

    def delete(self) -> None:
        sendable_ids_set = set(self.valid_items.values_list("id", flat=True))

        # Delete inbox "copies".
        self.valid_items.delete()

        if self.entity_settings.DELETE_HANGING_SENDABLES:
            Sendable = self.entity_settings.SENDABLE_CLASS
            content_type = ContentType.objects.get_for_model(Sendable)

            # Now that the received sendable references are deleted, those of their
            # respective sendables which are marked as removed from their senders'
            # outboxes, are no longer needed. Find the unreferenced ones by selecting
            # all referenced sendables, then get those of the queried ones that are not
            # in that set.

            referenced_sendable_ids = ReceivedSendable.objects.filter(
                content_type=content_type
            ).values("object_id")

            sendable_ids = Sendable.objects.filter(id__in=sendable_ids_set).values("id")

            unreferenced_sendable_ids = sendable_ids.difference(referenced_sendable_ids)

            # Delete unreferenced sendables which are removed from their outboxes,
            # along with their recipient-sendable association records.

            ids_for_deleting = Sendable.objects.filter(
                id__in=unreferenced_sendable_ids, is_removed=True
            ).values("id")

            RecipientSendableAssociation.objects.filter(
                object_id__in=ids_for_deleting, content_type=content_type
            ).delete()

            Sendable.objects.filter(id__in=ids_for_deleting).delete()


class DeleteSentSerializer(SelectSerializer):
    """Marks selected sent sendables as deleted."""

    user_role = "sender"
    removal_filters = {"is_removed": False}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.item_type = self.entity_settings.SENDABLE_CLASS

    def delete(self) -> None:
        if self.entity_settings.DELETE_HANGING_SENDABLES:
            Sendable = self.entity_settings.SENDABLE_CLASS
            content_type = ContentType.objects.get_for_model(Sendable)

            sendable_ids = self.valid_items.values("id")

            # Delete recipient-sendable association records.
            RecipientSendableAssociation.objects.filter(
                object_id__in=sendable_ids, content_type=content_type
            ).delete()

            # Mark as removed the queried sendables that are referenced by any inbox
            # "copies", and delete those that are not.

            referenced_sendable_ids = ReceivedSendable.objects.filter(
                content_type=content_type
            ).values("object_id")

            ids_for_marking = sendable_ids.intersection(referenced_sendable_ids)
            ids_for_deleting = sendable_ids.difference(referenced_sendable_ids)

            Sendable.objects.filter(id__in=ids_for_marking).update(is_removed=True)
            Sendable.objects.filter(id__in=ids_for_deleting).delete()

        else:
            self.valid_items.update(is_removed=True)
