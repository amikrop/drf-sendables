from typing import Any, Sequence, TypeVar, cast

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from tests.models import Sendable
from tests.types import TestCaseType
from tests.utils import (
    MessageMixin,
    NoticeMixin,
    SendableMixin,
    assert_forbidden,
    with_setting_changed,
)

Model = TypeVar("Model", Sendable, ReceivedSendable, RecipientSendableAssociation)

ReferenceModel = TypeVar(
    "ReferenceModel", ReceivedSendable, RecipientSendableAssociation
)

User = get_user_model()


class SendTests(TestCaseType):
    def send(self, content: str, *recipient_ids: int) -> Response:
        return self.client.post(
            self.url, data={"content": content, "recipient_ids": recipient_ids}
        )

    def assert_created(self, response: Response) -> None:
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def assert_no_other_records(
        self, model_class: type[Model], *instances: Model
    ) -> None:
        ids = [instance.id for instance in instances]
        other_instances = cast(Sequence, model_class.objects.exclude(id__in=ids))

        self.assertSequenceEqual(other_instances, [])

    def get_sole_record(self, model_class: type[Model]) -> Model:
        instance = cast(Model, model_class.objects.first())
        self.assert_no_other_records(model_class, instance)

        return instance

    def assert_records_exist_only_for_recipients(
        self,
        first_recipient: Any,
        second_recipient: Any,
        model_class: type[ReferenceModel],
        sendable: Sendable,
    ) -> None:
        first_record = model_class.objects.get(recipient=first_recipient)
        self.assertEqual(first_record.sendable, sendable)

        second_record = model_class.objects.get(recipient=second_recipient)
        self.assertEqual(second_record.sendable, sendable)

        self.assert_no_other_records(model_class, first_record, second_record)

    def test_send_success(self) -> None:
        CONTENT = "greetings"

        response = self.send(CONTENT, self.other_user.id)
        self.assert_created(response)
        self.assertEqual(
            response.data, {"content": CONTENT, "recipient_ids": [self.other_user.id]}
        )

        sendable = self.get_sole_record(cast(type[Sendable], self.sendable_class))
        self.assertEqual(sendable.content, CONTENT)

        if self.entity_name == "message":
            self.assertEqual(sendable.sender, self.user)  # type: ignore[attr-defined]

        received_sendable = self.get_sole_record(ReceivedSendable)
        self.assertEqual(received_sendable.sendable, sendable)
        self.assertEqual(received_sendable.recipient, self.other_user)

        association = self.get_sole_record(RecipientSendableAssociation)
        self.assertEqual(association.sendable, sendable)
        self.assertEqual(association.recipient, self.other_user)

    @assert_forbidden
    def test_send_forbidden(self) -> Response:
        return self.send("hello", self.other_user.id)

    def test_send_valid_and_invalid_ids_lenient(self) -> None:
        CONTENT = "Hello, world"
        some_recipient = User.objects.create_user(username="john")

        response = self.send(CONTENT, self.other_user.id, some_recipient.id, 450, 325)

        self.assert_created(response)
        self.assertEqual(
            response.data,
            {
                "content": CONTENT,
                "recipient_ids": [self.other_user.id, some_recipient.id],
            },
        )

        sendable = self.get_sole_record(cast(type[Sendable], self.sendable_class))
        self.assertEqual(sendable.content, CONTENT)

        self.assert_records_exist_only_for_recipients(
            self.other_user, some_recipient, ReceivedSendable, sendable
        )
        self.assert_records_exist_only_for_recipients(
            self.other_user, some_recipient, RecipientSendableAssociation, sendable
        )

    @with_setting_changed(
        "GET_VALID_RECIPIENTS",
        "sendables.core.policies.send.get_valid_recipients_strict",
    )
    def test_send_valid_and_invalid_ids_strict(self) -> None:
        INVALID_IDS = 333, 860, 501
        invalid_ids_display = ", ".join(str(id) for id in sorted(INVALID_IDS))

        response = self.send("sample", self.other_user.id, *INVALID_IDS)

        self.assert_bad_request_with_content(
            response,
            "recipient_ids",
            f"Invalid recipients: {invalid_ids_display}.",
            "invalid",
        )

    def test_send_no_valid_ids(self) -> None:
        for invalid_ids in [self.user.id, 730], [800, 268]:
            response = self.send("Some testing.", *invalid_ids)

            self.assert_bad_request_with_content(
                response, "recipient_ids", "No valid recipients.", "invalid"
            )

    def test_send_no_ids(self) -> None:
        response = self.send("hi")

        self.assert_bad_request_with_content(
            response, "recipient_ids", "This field is required.", "required"
        )

    def test_send_to_self(self) -> None:
        CONTENT = "A test"

        response = self.send(CONTENT, self.user.id)
        self.assert_bad_request(response)

        with self.setting_changed("ALLOW_SEND_TO_SELF", True):
            response = self.send(CONTENT, self.user.id)
            self.assert_created(response)


class SendableSendTests(SendTests, SendableMixin, APITestCase):
    action = "send"


class MessageSendTests(SendTests, MessageMixin, APITestCase):
    action = "send"


class NoticeSendTests(SendTests, NoticeMixin, APITestCase):
    action = "send"

    def test_send_non_admin_forbidden(self) -> None:
        self.client.force_authenticate(self.other_user)

        response = self.send("abc", self.user.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.user)
