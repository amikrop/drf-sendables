from django.apps import AppConfig

from sendables.core.settings import IMPORT_STRINGS, app_settings


def configure_messages_app() -> None:
    app_settings["message"] = {
        "SEND_SERIALIZER_CLASS": "sendables.messages.serializers.SendMessageSerializer",
        "SENDABLE_CLASS": "sendables.messages.models.Message",
        "LIST_SERIALIZER_CLASS": "sendables.messages.serializers.MessageListSerializer",
        "LIST_SENT_SERIALIZER_CLASS": (
            "sendables.messages.serializers.MessageSentSerializer"
        ),
        "DETAIL_SERIALIZER_CLASS": (
            "sendables.messages.serializers.MessageDetailSerializer"
        ),
        "DETAIL_SENT_SERIALIZER_CLASS": (
            "sendables.messages.serializers.MessageSentSerializer"
        ),
        "SENDER_FIELD_TYPE_LIST": (
            "sendables.messages.serializers.ParticipantSerializer"
        ),
        "SENDER_FIELD_TYPE_DETAIL": (
            "sendables.messages.serializers.ParticipantSerializer"
        ),
        "RECIPIENT_FIELD_TYPE_LIST": (
            "sendables.messages.serializers.ParticipantSerializer"
        ),
        "RECIPIENT_FIELD_TYPE_DETAIL": (
            "sendables.messages.serializers.ParticipantSerializer"
        ),
    }
    IMPORT_STRINGS.update(
        {
            "LIST_SENT_SERIALIZER_CLASS",
            "DETAIL_SENT_SERIALIZER_CLASS",
            "SENDER_FIELD_TYPE_LIST",
            "SENDER_FIELD_TYPE_DETAIL",
            "RECIPIENT_FIELD_TYPE_LIST",
            "RECIPIENT_FIELD_TYPE_DETAIL",
        }
    )


class SendablesMessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sendables.messages"
    label = "sendables_messages"

    def ready(self) -> None:
        configure_messages_app()
