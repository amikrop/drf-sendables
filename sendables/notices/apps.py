from django.apps import AppConfig

from sendables.core.settings import app_settings


def configure_notices_app() -> None:
    app_settings["notice"] = {
        "SENDABLE_CLASS": "sendables.notices.models.Notice",
        "SEND_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
    }


class SendablesNoticesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sendables.notices"
    label = "sendables_notices"

    def ready(self) -> None:
        configure_notices_app()
