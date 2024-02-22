from django.apps import AppConfig

from sendables.messages.apps import configure_messages_app
from sendables.notices.apps import configure_notices_app


class SendablesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sendables"

    def ready(self) -> None:
        configure_messages_app()
        configure_notices_app()
