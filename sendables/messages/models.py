from django.conf import settings
from django.db import models

from sendables.core.models import Sendable
from sendables.core.utils import conditionally_concrete


@conditionally_concrete
class Message(Sendable):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sent_messages",
    )

    class Meta:
        abstract = True
