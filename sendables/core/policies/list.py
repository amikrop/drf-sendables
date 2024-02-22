from typing import cast

from sendables.core.models import (
    ReceivedSendable,
    RecipientSendableAssociation,
    Sendable,
)
from sendables.core.types import ManagedModel


def get_received_prefetch_fields(sendable_class: type[ManagedModel]) -> list[str]:
    """Provide "prefetch related" fields for received sendable list.

    Pick `sendable` (the sendable record reference), and if there is a `sender` field
    on `sendable` pick that relation as well.

    Args:
        sendable_class: The sendable model class

    Returns:
        The chosen "prefetch related" fields
    """
    result = ["sendable"]

    if hasattr(sendable_class, "sender"):
        result.append("sendable__sender")

    return result


def sort_received_key(received_sendable: ReceivedSendable) -> tuple[bool, float]:
    """Get sorting key for received sendables.

    Utilized to sort received sendables.
    Sort first by "is read" ascending, then by "sent on" descending.

    Args:
        received_sendable: The received sendable

    Returns:
        The comparison tuple
    """
    sendable = cast(Sendable, received_sendable.sendable)

    return received_sendable.is_read, -sendable.sent_on.timestamp()


def sort_sent_key(association: RecipientSendableAssociation) -> float:
    """Get sorting key for recipient-sendable associations.

    Utilized to sort sent sendables.
    Sort by "sent on" descending.

    Args:
        association: The recipient-sendable association

    Returns:
        The comparison value
    """
    sendable = cast(Sendable, association.sendable)

    return -sendable.sent_on.timestamp()
