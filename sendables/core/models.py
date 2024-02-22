from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from sendables.core.types import ManagedModel
from sendables.core.utils import conditionally_concrete


@conditionally_concrete
class Sendable(ManagedModel, models.Model):
    content = models.TextField()
    is_removed = models.BooleanField(
        default=False,
        help_text="Whether the sendable is marked as deleted from its sender's outbox.",
    )
    sent_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ReceivedSendable(ManagedModel, models.Model):
    """Reference to some sendable, in a user's inbox (their own "copy")."""

    is_read = models.BooleanField(default=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    sendable = GenericForeignKey()

    class Meta:
        indexes = [models.Index(fields=["content_type", "object_id"])]


class RecipientSendableAssociation(ManagedModel, models.Model):
    """Connection between recipient and sendable sent to them (who a sendable
    was sent to).
    """

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    sendable = GenericForeignKey()

    class Meta:
        indexes = [models.Index(fields=["content_type", "object_id"])]
