from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
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


class DetailTests(FixturesMixin):
    view_name_suffix = ""

    def get(self, received_sendable_id: int) -> Response:
        url = reverse(
            f"{self.entity_name}-detail{self.view_name_suffix}",
            kwargs={"id": received_sendable_id},
        )
        return self.client.get(url)

    def validate(
        self, record: ReceivedSendable | Sendable, expected_data: dict[str, Any]
    ) -> None:
        response = self.get(record.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_id_and_sent_on(response.data)

        expected_result = self.get_expected_data(expected_data)
        self.assertDictEqual(response.data, expected_result)

    def get_tested_record(self, sendable: Sendable) -> ReceivedSendable | Sendable:
        content_type = ContentType.objects.get_for_model(sendable.__class__)
        return ReceivedSendable.objects.get(
            object_id=sendable.id, content_type=content_type
        )

    def test_detail_success(self) -> None:
        sendable = self.sendable_class.objects.get(content=self.CONTENT_SINGLE)
        record = self.get_tested_record(sendable)

        self.validate(record, {"content": self.CONTENT_SINGLE})

    @assert_forbidden
    def test_detail_forbidden(self) -> Response:
        sendable = self.sendable_class.objects.get(content=self.CONTENT_SINGLE)
        record = self.get_tested_record(sendable)

        return self.get(record.id)

    def test_detail_not_found(self) -> None:
        response = self.get(1700)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_not_owned(self) -> None:
        received_sendable = ReceivedSendable.objects.get(recipient=self.other_user)
        response = self.get(received_sendable.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def validate_slugged(self, content: str, slug: str) -> None:
        sendable = self.create_sendable(content, slug=slug)
        self.add_to_recipients(sendable)
        record = self.get_tested_record(sendable)

        self.validate(record, {"content": content, "slug": slug})

    def test_detail_custom_model_and_serializer(self) -> None:
        class_name = self.slugged_sendable_class.__name__
        with self.setting_changed("SENDABLE_CLASS", "tests.models." + class_name):
            with self.setting_changed(
                "DETAIL_SERIALIZER_CLASS",
                "tests.utils." + self.slugged_serializer_class,
            ):
                self.validate_slugged("The text.", "text")


class SendableDetailTests(DetailTests, SendableMixin, APITestCase):
    pass


class MessageDetailTests(DetailTests, MessageMixin, APITestCase):
    pass


class NoticeDetailTests(DetailTests, NoticeMixin, APITestCase):
    pass
