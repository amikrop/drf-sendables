from typing import Sequence, cast

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from tests.models import Sendable
from tests.utils import (
    FixturesMixin,
    MessageMixin,
    NoticeMixin,
    SendableMixin,
    assert_forbidden,
    with_setting_changed,
)


class DeleteTests(FixturesMixin):
    def delete(self, received_sendable_ids: QuerySet | Sequence) -> Response:
        return self.client.delete(
            self.url, data={self.entity_name + "_ids": received_sendable_ids}
        )

    def get_records(
        self, remove_first_sendable: bool = True
    ) -> tuple[QuerySet, QuerySet, list, int, int, Sendable | None]:
        received_sendables = ReceivedSendable.objects.filter(
            recipient=self.user
        ).prefetch_related("sendable")

        received_sendable_ids = received_sendables.values_list("id", flat=True)
        sendable_ids = [
            received_sendable.sendable.id  # type: ignore[union-attr]
            for received_sendable in received_sendables
        ]

        starting_sendables_count = len(sendable_ids)
        starting_associations_count = RecipientSendableAssociation.objects.filter(
            object_id__in=sendable_ids, content_type=self.content_type
        ).count()

        removed_sendable = None

        if remove_first_sendable:
            removed_sendable = cast(Sendable, received_sendables[0].sendable)
            removed_sendable.is_removed = True
            removed_sendable.save()

        return (
            received_sendables,
            received_sendable_ids,
            sendable_ids,
            starting_sendables_count,
            starting_associations_count,
            removed_sendable,
        )

    def check_entities_deleted(
        self,
        sendable_ids: list,
        received_sendable_ids: QuerySet,
        expected_sendables_count: int,
        expected_associations_count: int,
    ) -> None:
        response = self.delete(received_sendable_ids)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        remaining_received_sendables = cast(
            Sequence, ReceivedSendable.objects.filter(id__in=received_sendable_ids)
        )
        self.assertSequenceEqual(remaining_received_sendables, [])

        sendables_count = self.sendable_class.objects.filter(
            id__in=sendable_ids
        ).count()
        self.assertEqual(sendables_count, expected_sendables_count)

        associations_count = RecipientSendableAssociation.objects.filter(
            object_id__in=sendable_ids, content_type=self.content_type
        ).count()
        self.assertEqual(associations_count, expected_associations_count)

    def test_delete_success(self) -> None:
        (
            _,
            received_sendable_ids,
            sendable_ids,
            starting_sendables_count,
            starting_associations_count,
            _,
        ) = self.get_records(remove_first_sendable=False)

        self.check_entities_deleted(
            sendable_ids,
            received_sendable_ids,
            starting_sendables_count,
            starting_associations_count,
        )

    @assert_forbidden
    def test_delete_forbidden(self) -> Response:
        _, received_sendable_ids, *_ = self.get_records(remove_first_sendable=False)

        return self.delete(received_sendable_ids)

    def get_not_owned_id(self) -> int:
        not_owned_record = ReceivedSendable.objects.get(recipient=self.other_user)
        return not_owned_record.id

    def test_delete_valid_and_invalid_ids_lenient(self) -> None:
        received_sendable_ids = ReceivedSendable.objects.filter(
            recipient=self.user
        ).values_list("id", flat=True)

        not_owned_id = self.get_not_owned_id()

        queried_ids = *received_sendable_ids, not_owned_id, 875

        response = self.delete(queried_ids)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        remaining_received_sendables = cast(
            Sequence, ReceivedSendable.objects.filter(id__in=received_sendable_ids)
        )
        self.assertSequenceEqual(remaining_received_sendables, [])

        ReceivedSendable.objects.get(id=not_owned_id)

    @with_setting_changed(
        "GET_VALID_ITEMS", "sendables.core.policies.select.get_valid_items_strict"
    )
    def test_delete_valid_and_invalid_ids_strict(self) -> None:
        received_sendable_ids = ReceivedSendable.objects.filter(
            recipient=self.user
        ).values_list("id", flat=True)

        starting_records_count = len(received_sendable_ids)

        not_owned_id = self.get_not_owned_id()

        queried_ids = *received_sendable_ids, not_owned_id

        response = self.delete(queried_ids)
        self.assert_bad_request_with_content(
            response,
            self.entity_name + "_ids",
            f"Invalid {self.entity_name}s: {not_owned_id}.",
            "invalid",
        )

        records_count = ReceivedSendable.objects.filter(
            id__in=received_sendable_ids
        ).count()
        self.assertEqual(records_count, starting_records_count)

        ReceivedSendable.objects.get(id=not_owned_id)

    def test_delete_no_valid_ids(self) -> None:
        not_owned_id = self.get_not_owned_id()

        for invalid_ids in [not_owned_id], [300, 111, 600]:
            response = self.delete(invalid_ids)

            self.assert_bad_request_with_content(
                response,
                self.entity_name + "_ids",
                f"No valid {self.entity_name}s.",
                "invalid",
            )

    def test_delete_no_ids(self) -> None:
        response = self.delete([])

        self.assert_bad_request_with_content(
            response, self.entity_name + "_ids", "This field is required.", "required"
        )

    def test_delete_removed_sendable(self) -> None:
        (
            _,
            received_sendable_ids,
            sendable_ids,
            starting_sendables_count,
            starting_associations_count,
            removed_sendable,
        ) = self.get_records()

        self.check_entities_deleted(
            sendable_ids,
            received_sendable_ids,
            starting_sendables_count - 1,
            starting_associations_count - 1,
        )

        removed_sendable = cast(Sendable, removed_sendable)

        sendables_with_id_of_removed = cast(
            Sequence, Sendable.objects.filter(id=removed_sendable.id)
        )
        self.assertSequenceEqual(sendables_with_id_of_removed, [])

        associations_with_sendable_id_of_removed = cast(
            Sequence,
            RecipientSendableAssociation.objects.filter(
                object_id=removed_sendable.id, content_type=self.content_type
            ),
        )
        self.assertSequenceEqual(associations_with_sendable_id_of_removed, [])

    @with_setting_changed("DELETE_HANGING_SENDABLES", False)
    def test_delete_removed_sendable_without_delete_hanging(self) -> None:
        (
            _,
            received_sendable_ids,
            sendable_ids,
            starting_sendables_count,
            starting_associations_count,
            _,
        ) = self.get_records()

        self.check_entities_deleted(
            sendable_ids,
            received_sendable_ids,
            starting_sendables_count,
            starting_associations_count,
        )

    def test_delete_removed_sendable_referenced(self) -> None:
        (
            _,
            received_sendable_ids,
            sendable_ids,
            starting_sendables_count,
            starting_associations_count,
            removed_sendable,
        ) = self.get_records()

        ReceivedSendable.objects.create(
            recipient=self.other_user, sendable=removed_sendable
        )

        self.check_entities_deleted(
            sendable_ids,
            received_sendable_ids,
            starting_sendables_count,
            starting_associations_count,
        )


class SendableDeleteTests(DeleteTests, SendableMixin, APITestCase):
    action = "delete"


class MessageDeleteTests(DeleteTests, MessageMixin, APITestCase):
    action = "delete"


class NoticeDeleteTests(DeleteTests, NoticeMixin, APITestCase):
    action = "delete"
