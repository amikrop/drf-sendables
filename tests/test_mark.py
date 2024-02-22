from typing import cast

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from sendables.core.models import ReceivedSendable
from tests.types import TestCaseType
from tests.utils import (
    MessageMixin,
    NoticeMixin,
    SendableMixin,
    assert_forbidden,
    with_setting_changed,
)


class MarkAsReadTests(TestCaseType):
    url: str
    is_read = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        state = "read" if cls.is_read else "unread"
        cls.url = reverse(f"{cls.entity_name}-mark-{state}")

    def setUp(self) -> None:
        super().setUp()
        self.received_sendable_ids: list[list[int]] = [[], []]

        for is_read in self.is_read, not self.is_read:
            for i in range(2):
                is_read_display = "read" if is_read else "unread"
                sendable = self.sendable_class.objects.create(
                    content=f"Hello from {is_read_display} sendable #{i}!"
                )
                received_sendable = ReceivedSendable.objects.create(
                    recipient=self.user, sendable=sendable, is_read=is_read
                )
                self.received_sendable_ids[is_read].append(received_sendable.id)

    def mark(self, received_sendable_ids: list[int]) -> Response:
        return self.client.patch(
            self.url, data={self.entity_name + "_ids": received_sendable_ids}
        )

    def assert_ok(self, response: Response) -> None:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)

    def assert_have_state(
        self, received_sendable_ids: list[int], have_view_state: bool = True
    ) -> None:
        state = self.is_read if have_view_state else not self.is_read
        received_sendables = ReceivedSendable.objects.filter(
            object_id__in=received_sendable_ids, content_type=self.content_type
        )
        for received_sendable in received_sendables:
            self.assertEqual(received_sendable.is_read, state)

    def test_mark_success(self) -> None:
        records_to_change = self.received_sendable_ids[not self.is_read]
        records_to_remain = self.received_sendable_ids[self.is_read]
        queried_ids = [*records_to_change, *records_to_remain]

        response = self.mark(queried_ids)

        self.assert_ok(response)
        self.assert_have_state(queried_ids)

    @assert_forbidden
    def test_mark_forbidden(self) -> Response:
        return self.mark([1, 2])

    def get_sample_ids(self, content: str) -> tuple[int, int, int]:
        different_state = not self.is_read
        sendable = self.sendable_class.objects.create(content=content)
        received_sendable_not_owned = ReceivedSendable.objects.create(
            recipient=self.other_user, sendable=sendable, is_read=different_state
        )
        valid_ids = self.received_sendable_ids[not self.is_read]

        result = *valid_ids, received_sendable_not_owned.id
        return cast(tuple[int, int, int], result)

    def test_mark_valid_and_invalid_ids_lenient(self) -> None:
        *valid_ids, not_owned_id = self.get_sample_ids("foo bar")

        response = self.mark([*valid_ids, 632, not_owned_id])

        self.assert_ok(response)
        self.assert_have_state(valid_ids)
        self.assert_have_state([not_owned_id], have_view_state=False)

    @with_setting_changed(
        "GET_VALID_ITEMS", "sendables.core.policies.select.get_valid_items_strict"
    )
    def test_mark_valid_and_invalid_ids_strict(self) -> None:
        *valid_ids, not_owned_id = self.get_sample_ids("123 456")

        response = self.mark([*valid_ids, not_owned_id])

        self.assert_bad_request_with_content(
            response,
            self.entity_name + "_ids",
            f"Invalid {self.entity_name}s: {not_owned_id}.",
            "invalid",
        )
        self.assert_have_state(valid_ids, have_view_state=False)
        self.assert_have_state([not_owned_id], have_view_state=False)

    def test_mark_no_valid_ids(self) -> None:
        *_, not_owned_id = self.get_sample_ids("abc")
        for invalid_ids in [not_owned_id, 444], [239, 1001]:
            response = self.mark(invalid_ids)

            self.assert_bad_request_with_content(
                response,
                self.entity_name + "_ids",
                f"No valid {self.entity_name}s.",
                "invalid",
            )

    def test_mark_no_ids(self) -> None:
        response = self.mark([])

        self.assert_bad_request_with_content(
            response, self.entity_name + "_ids", "This field is required.", "required"
        )


class MarkAsUnreadTests(MarkAsReadTests):
    is_read = False


class SendableMarkAsReadTests(MarkAsReadTests, SendableMixin, APITestCase):
    pass


class SendableMarkAsUnreadTests(MarkAsUnreadTests, SendableMixin, APITestCase):
    pass


class MessageMarkAsReadTests(MarkAsReadTests, MessageMixin, APITestCase):
    pass


class MessageMarkAsUnreadTests(MarkAsUnreadTests, MessageMixin, APITestCase):
    pass


class NoticeMarkAsReadTests(MarkAsReadTests, NoticeMixin, APITestCase):
    pass


class NoticeMarkAsUnreadTests(MarkAsUnreadTests, NoticeMixin, APITestCase):
    pass
