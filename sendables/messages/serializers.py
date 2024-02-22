from typing import Any, Iterable, cast

from rest_framework import exceptions, serializers

from sendables.core.serializers import ReceivedSendableSerializer, SendSerializer
from sendables.core.settings import app_settings


class ReceivedMessageSerializer(ReceivedSendableSerializer):
    sender_field_type_setting: str

    def get_fields(self) -> dict[str, serializers.Field]:
        """Dynamically add the sender field."""
        fields = super().get_fields()
        settings = app_settings[self.context["entity_name"]]

        sender_field_type = getattr(settings, self.sender_field_type_setting)
        fields["sender"] = sender_field_type(source="sendable.sender")

        return fields


class MessageListSerializer(ReceivedMessageSerializer):
    sender_field_type_setting = "SENDER_FIELD_TYPE_LIST"


class MessageDetailSerializer(ReceivedMessageSerializer):
    sender_field_type_setting = "SENDER_FIELD_TYPE_DETAIL"


class MessageSentParentSerializer(serializers.ListSerializer):
    """Groups recipient-sendable association records under their common sendables."""

    def in_detail_view(self) -> bool:
        return cast(bool, self.context["view"].__class__.__name__ == "DetailSentView")

    def to_representation(
        self, association_data: Iterable  # type: ignore[override]
    ) -> list[dict[str, Any]]:
        """Construct a list of dicts, each containing data for a sent sendable,
        including a list of recipients.
        """
        settings = app_settings[self.context["entity_name"]]

        # Sendable id, to sendable data
        sendables = {}
        # Sendable id, to recipient list
        recipients: dict[int, list[dict[str, Any]]] = {}

        for record in association_data:
            if (sendable_id := record.sendable.id) not in sendables:
                # Newly encountered sendable id, generate its data and create empty
                # recipient list.
                data = self.child.to_representation(record)  # type: ignore[union-attr]
                sendables[sendable_id] = data
                recipients[sendable_id] = []

            # Get recipient representation according to settings and add it to its
            # respective sendable's list. Use appropriate setting for list view or
            # detail view.
            field_type = (
                settings.RECIPIENT_FIELD_TYPE_DETAIL
                if self.in_detail_view()
                else settings.RECIPIENT_FIELD_TYPE_LIST
            )
            field = field_type(context=self.context)
            recipients[sendable_id].append(field.to_representation(record.recipient))

        for sendable_id, sendable_data in sendables.items():
            sendable_data["recipients"] = recipients[sendable_id]

        return cast(list[dict[str, Any]], sendables.values())

    @property
    def data(self) -> Any:
        """Return list of items for list view, single item for detail view, 404 response
        if no accessible data found.
        """
        result = super().data
        if self.in_detail_view():
            try:
                return result[0]
            except IndexError:
                raise exceptions.NotFound

        return result


class MessageSentSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="sendable.id")
    content = serializers.CharField(source="sendable.content")
    sent_on = serializers.DateTimeField(source="sendable.sent_on")

    class Meta:
        list_serializer_class = MessageSentParentSerializer


class SendMessageSerializer(SendSerializer):
    def save(self, **kwargs: Any) -> None:
        # While saving, include current user as the sender of the message.
        super().save(sender=self.context["request"].user)


class ParticipantSerializer(serializers.Serializer):
    def get_fields(self) -> dict[str, serializers.Field]:
        """Dynamically add a uniquely identifying field, and the username if not already
        present.
        """
        fields = super().get_fields()
        settings = app_settings[self.context["entity_name"]]

        fields[settings.PARTICIPANT_KEY_NAME] = settings.PARTICIPANT_KEY_TYPE()
        if "username" not in fields:
            fields["username"] = serializers.CharField()

        return fields
