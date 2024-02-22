from typing import Sequence

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from tests.utils import (
    FixturesMixin,
    MessageMixin,
    TestSentMixin,
    assert_forbidden,
    with_setting_changed,
)


class MessageDeleteSentTests(TestSentMixin, FixturesMixin, MessageMixin, APITestCase):
    action = "delete-sent"

    def assertQuerySetEqual(  # type: ignore[override]
        self, queryset: QuerySet, expected_queryset: QuerySet
    ) -> None:
        try:
            super().assertQuerySetEqual(queryset, expected_queryset)
        except AttributeError:
            expected_list = list(expected_queryset)
            if (
                len(expected_list) > 1
                and hasattr(queryset, "ordered")
                and not queryset.ordered
            ):
                raise ValueError(
                    "Trying to compare non-ordered queryset against more than one "
                    "ordered value."
                )
            self.assertEqual(list(queryset), expected_list)

    def delete(self, sendable_ids: Sequence[int], assert_ok: bool = True) -> Response:
        response = self.client.delete(
            self.url, data={self.entity_name + "_ids": sendable_ids}
        )
        if assert_ok:
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        return response

    def get_records(
        self, assert_removed: bool = False
    ) -> tuple[tuple, QuerySet, QuerySet, QuerySet]:
        sendables = self.sendable_class.objects.filter(sender=self.sender).order_by(
            "id"
        )
        sendable_ids = sendables.values_list("id", flat=True)

        received_sendables = ReceivedSendable.objects.filter(
            object_id__in=sendable_ids, content_type=self.content_type
        ).order_by("id")

        associations = RecipientSendableAssociation.objects.filter(
            object_id__in=sendable_ids, content_type=self.content_type
        ).order_by("id")

        assert_method = self.assertTrue if assert_removed else self.assertFalse
        for sendable in sendables:
            assert_method(sendable.is_removed)

        return tuple(sendable_ids), sendables, received_sendables, associations

    def test_delete_sent_success(self) -> None:
        sendable_ids, sendables, received_sendables, _ = self.get_records()

        self.delete(sendable_ids)

        _, result_sendables, result_received_sendables, result_associations = (
            self.get_records(assert_removed=True)
        )

        self.assertQuerySetEqual(result_sendables, sendables)
        self.assertQuerySetEqual(result_received_sendables, received_sendables)
        self.assertQuerySetEqual(
            result_associations, RecipientSendableAssociation.objects.none()
        )

    @assert_forbidden
    def test_delete_sent_forbidden(self) -> Response:
        sendable_ids, *_ = self.get_records()

        return self.delete(sendable_ids, assert_ok=False)

    def get_not_owned_id(self) -> int:
        not_owned_record = self.sendable_class.objects.create(
            content="321", sender=self.user
        )
        return not_owned_record.id

    def test_delete_sent_valid_and_invalid_ids_lenient(self) -> None:
        sendable_ids, sendables, received_sendables, _ = self.get_records()

        not_owned_id = self.get_not_owned_id()

        queried_ids = *sendable_ids, not_owned_id, 207

        self.delete(queried_ids)

        _, result_sendables, result_received_sendables, result_associations = (
            self.get_records(assert_removed=True)
        )

        self.assertQuerySetEqual(result_sendables, sendables)
        self.assertQuerySetEqual(result_received_sendables, received_sendables)
        self.assertQuerySetEqual(
            result_associations, RecipientSendableAssociation.objects.none()
        )

        self.sendable_class.objects.get(id=not_owned_id)

    @with_setting_changed(
        "GET_VALID_ITEMS", "sendables.core.policies.select.get_valid_items_strict"
    )
    def test_delete_sent_valid_and_invalid_ids_strict(self) -> None:
        sendable_ids, sendables, received_sendables, associations = self.get_records()

        not_owned_id = self.get_not_owned_id()
        non_existent_ids = 600, 700

        queried_ids = not_owned_id, *sendable_ids, *non_existent_ids

        invalid_ids = sorted([not_owned_id, *non_existent_ids])
        invalid_ids_display = ", ".join(map(str, invalid_ids))

        response = self.delete(queried_ids, assert_ok=False)
        expected_error_message = f"Invalid {self.entity_name}s: {invalid_ids_display}."
        self.assert_bad_request_with_content(
            response, self.entity_name + "_ids", expected_error_message, "invalid"
        )

        _, result_sendables, result_received_sendables, result_associations = (
            self.get_records()
        )

        self.assertQuerySetEqual(result_sendables, sendables)
        self.assertQuerySetEqual(result_received_sendables, received_sendables)
        self.assertQuerySetEqual(result_associations, associations)

        self.sendable_class.objects.get(id=not_owned_id)

    def test_delete_sent_no_valid_ids(self) -> None:
        not_owned_id = self.get_not_owned_id()

        for invalid_ids in [not_owned_id], [987, 432]:
            response = self.delete(invalid_ids, assert_ok=False)

            self.assert_bad_request_with_content(
                response,
                self.entity_name + "_ids",
                f"No valid {self.entity_name}s.",
                "invalid",
            )

    def test_delete_sent_no_ids(self) -> None:
        response = self.delete([], assert_ok=False)

        self.assert_bad_request_with_content(
            response, self.entity_name + "_ids", "This field is required.", "required"
        )

    def delete_sample_records(
        self, sendable_ids: tuple, received_sendables: QuerySet
    ) -> tuple[int, list[int]]:
        sendable_id_to_delete = sendable_ids[0]

        received_sendable_ids_to_delete = [
            received_sendable.id
            for received_sendable in received_sendables
            if received_sendable.sendable.id == sendable_id_to_delete
        ]
        ReceivedSendable.objects.filter(id__in=received_sendable_ids_to_delete).delete()

        self.delete([sendable_id_to_delete, sendable_ids[1]])

        return sendable_id_to_delete, received_sendable_ids_to_delete

    def test_delete_sent_no_received(self) -> None:
        sendable_ids, _, received_sendables, _ = self.get_records()

        sendable_id_to_delete, received_sendable_ids_to_delete = (
            self.delete_sample_records(sendable_ids, received_sendables)
        )

        _, result_sendables, result_received_sendables, result_associations = (
            self.get_records(assert_removed=True)
        )

        expected_sendables = (
            self.sendable_class.objects.filter(sender=self.sender)
            .exclude(id=sendable_id_to_delete)
            .order_by("id")
        )
        self.assertQuerySetEqual(result_sendables, expected_sendables)

        expected_received_sendables = ReceivedSendable.objects.exclude(
            id__in=received_sendable_ids_to_delete
        ).order_by("id")
        self.assertQuerySetEqual(result_received_sendables, expected_received_sendables)

        self.assertQuerySetEqual(
            result_associations, RecipientSendableAssociation.objects.none()
        )

    @with_setting_changed("DELETE_HANGING_SENDABLES", False)
    def test_delete_sent_no_received_without_delete_hanging(self) -> None:
        sendable_ids, sendables, received_sendables, associations = self.get_records()

        _, received_sendable_ids_to_delete = self.delete_sample_records(
            sendable_ids, received_sendables
        )

        _, result_sendables, result_received_sendables, result_associations = (
            self.get_records(assert_removed=True)
        )

        self.assertQuerySetEqual(result_sendables, sendables)

        expected_received_sendables = ReceivedSendable.objects.exclude(
            id__in=received_sendable_ids_to_delete
        ).order_by("id")
        self.assertQuerySetEqual(result_received_sendables, expected_received_sendables)

        self.assertQuerySetEqual(result_associations, associations)
