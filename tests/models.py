from django.conf import settings
from django.db import models

from sendables.core.models import Sendable as SendableAbstract
from sendables.messages.models import Message as MessageAbstract
from sendables.notices.models import Notice as NoticeAbstract


class Sendable(SendableAbstract):
    pass


class SluggedSendable(SendableAbstract):
    slug = models.SlugField()


class Message(MessageAbstract):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sent_test_messages",
    )


class SluggedMessage(MessageAbstract):
    slug = models.SlugField()
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="sent_slugged_test_messages",
    )


class Notice(NoticeAbstract):
    pass


class SluggedNotice(NoticeAbstract):
    slug = models.SlugField()
