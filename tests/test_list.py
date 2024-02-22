from typing import Any, cast

from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.test import APITestCase

from sendables.core.models import ReceivedSendable
from tests.models import Sendable
from tests.utils import (
    FixturesMixin,
    MessageMixin,
    NoticeMixin,
    SendableMixin,
    assert_forbidden,
)


class ListTests(FixturesMixin):
    list_type = "LIST"
    sort_key = "SORT_RECEIVED_KEY"

    def validate_items(self, response: Response, items: list[dict[str, Any]]) -> None:
        self.assertEqual(len(response.data), len(items))

        expected_items = [self.get_expected_data(item) for item in items]
        for data_item in response.data:
            self.check_id_and_sent_on(data_item)
            self.assertIn(data_item, expected_items)

    def assert_contents_in(self, response: Response, *content_list: str) -> None:
        items = [{"content": content} for content in content_list]
        self.validate_items(response, items)

    def get(self, **query_params: Any) -> Response:
        response = self.client.get(self.url, data=query_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        return response

    def test_list_success(self) -> None:
        response = self.get()
        self.assert_contents_in(response, self.CONTENT_SINGLE, self.CONTENT_MULTIPLE)

    @assert_forbidden
    def test_list_forbidden(self) -> Response:
        return self.client.get(self.url)

    def validate_slugged(self, content: str, slug: str) -> None:
        for i in range(3):
            sendable = self.create_sendable(
                content.format(i + 1), slug=slug.format(i + 1)
            )
            self.add_to_recipients(sendable)

            response = self.get()

        items = [
            {"content": content.format(i + 1), "slug": slug.format(i + 1)}
            for i in range(3)
        ]
        self.validate_items(response, items)

    def test_list_custom_model_and_serializer(self) -> None:
        class_name = self.slugged_sendable_class.__name__
        with self.setting_changed("SENDABLE_CLASS", "tests.models." + class_name):
            with self.setting_changed(
                "LIST_SERIALIZER_CLASS",
                "tests.utils." + self.slugged_serializer_class,
            ):
                self.validate_slugged("Hi, this is sendable {}.", "sendable{}")

    def test_list_search_content(self) -> None:
        CONTENT = self.CONTENT_SINGLE[:5]
        response = self.get(content=CONTENT)

        self.assert_contents_in(response, self.CONTENT_SINGLE)

    def test_list_search_sent_on(self) -> None:
        CONTENT = "late message"
        now_timestamp = timezone.now().timestamp()

        self.send_sendable(CONTENT)

        response = self.get(sent_on__gt=now_timestamp)

        self.assert_contents_in(response, CONTENT)

    def test_list_search_or(self) -> None:
        CONTENT_FIRST_TERM = self.CONTENT_SINGLE[:5]
        CONTENT_SECOND_TERM = self.CONTENT_MULTIPLE[:6]

        self.send_sendable(".....")

        response = self.get(content=[CONTENT_FIRST_TERM, CONTENT_SECOND_TERM])

        self.assert_contents_in(response, self.CONTENT_SINGLE, self.CONTENT_MULTIPLE)

    def test_list_search_and(self) -> None:
        CONTENT = self.CONTENT_SINGLE[:5]

        self.send_sendable(CONTENT)

        now_timestamp = timezone.now().timestamp()

        self.send_sendable(CONTENT)

        response = self.get(content=CONTENT, sent_on__lte=now_timestamp)

        self.assert_contents_in(response, self.CONTENT_SINGLE, CONTENT)

    def test_list_search_or_and(self) -> None:
        CONTENT_FIRST_TERM = self.CONTENT_SINGLE[:5]
        CONTENT_SECOND_TERM = self.CONTENT_MULTIPLE[:6]

        self.send_sendable(CONTENT_FIRST_TERM)
        self.send_sendable("blah")

        now_timestamp = timezone.now().timestamp()

        self.send_sendable(CONTENT_FIRST_TERM)

        response = self.get(
            content=[CONTENT_FIRST_TERM, CONTENT_SECOND_TERM],
            sent_on__lte=now_timestamp,
        )

        self.assert_contents_in(
            response, self.CONTENT_SINGLE, self.CONTENT_MULTIPLE, CONTENT_FIRST_TERM
        )

    def check_list_paginated(self, setting_key: str) -> None:
        class Pagination(PageNumberPagination):
            page_size = 10

        with self.setting_changed(setting_key, Pagination):
            for _ in range(Pagination.page_size * 3):
                self.send_sendable("test")

            response = self.get(page=2)

        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), Pagination.page_size)

    def test_list_paginated(self) -> None:
        self.check_list_paginated("PAGINATION_CLASS")
        self.check_list_paginated(self.list_type + "_PAGINATION_CLASS")

    def test_list_default_ordering(self) -> None:
        CONTENT = "some content"

        sendable = cast(
            Sendable,
            self.sendable_class.objects.filter(content=self.CONTENT_SINGLE).first(),
        )
        received_sendable = ReceivedSendable.objects.get(id=sendable.id)
        received_sendable.is_read = True
        received_sendable.save()

        self.send_sendable(CONTENT)

        response = self.get()

        expected_count = 2 if self.list_type == "LIST_UNREAD" else 3

        self.assertEqual(len(response.data), expected_count)
        self.assertEqual(response.data[0]["content"], CONTENT)
        self.assertEqual(response.data[1]["content"], self.CONTENT_MULTIPLE)
        if expected_count == 3:
            self.assertEqual(response.data[2]["content"], self.CONTENT_SINGLE)

    def test_list_custom_ordering(self) -> None:
        CONTENT = "Nice"

        def sort_received_key(received_sendable: ReceivedSendable) -> str:
            sendable = cast(Sendable, received_sendable.sendable)
            return sendable.content

        self.send_sendable(CONTENT)

        with self.setting_changed(self.sort_key, sort_received_key):
            response = self.get()

        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["content"], self.CONTENT_SINGLE)
        self.assertEqual(response.data[1]["content"], CONTENT)
        self.assertEqual(response.data[2]["content"], self.CONTENT_MULTIPLE)


class SendableListTests(ListTests, SendableMixin, APITestCase):
    action = "list"


class MessageListTests(ListTests, MessageMixin, APITestCase):
    action = "list"


class NoticeListTests(ListTests, NoticeMixin, APITestCase):
    action = "list"
