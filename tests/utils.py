from contextlib import contextmanager
from datetime import datetime
from functools import partial
from typing import Any, Callable, Generator, cast

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.functional import cached_property
from rest_framework import serializers, status
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response

from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from sendables.core.models import Sendable as SendableAbstract
from sendables.core.serializers import ReceivedSendableSerializer
from sendables.core.settings import _maybe_import, app_settings
from sendables.messages.serializers import (
    MessageDetailSerializer,
    MessageSentSerializer,
)
from tests.models import (
    Message,
    Notice,
    Sendable,
    SluggedMessage,
    SluggedNotice,
    SluggedSendable,
)
from tests.types import TestCaseType

User = get_user_model()


class TestMixin(TestCaseType):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        app_settings[cls.entity_name].SENDABLE_CLASS = cls.sendable_class

        if hasattr(cls, "action"):
            cls.url = reverse(f"{cls.entity_name}-{cls.action}")

        cls.content_type = ContentType.objects.get_for_model(cls.sendable_class)

    def setUp(self) -> None:
        self.user = User.objects.create_user(username="bob")
        self.other_user = User.objects.create_user(username="alice")

        self.client.force_authenticate(self.user)

    @contextmanager
    def setting_changed(self, key: str, value: Any) -> Generator:
        entity_settings = app_settings[self.entity_name]

        original_value = getattr(entity_settings, key)
        value = _maybe_import(key, value)
        setattr(entity_settings, key, value)

        try:
            yield
        finally:
            setattr(entity_settings, key, original_value)

    def assert_bad_request(self, response: Response) -> None:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def assert_bad_request_with_content(
        self, response: Response, field_name: str, message: str, code: str
    ) -> None:
        self.assert_bad_request(response)
        self.assertEqual(response.data, {field_name: [ErrorDetail(message, code)]})


class FixturesMixin(TestCaseType):
    is_read = False
    _slugged_serializer_class = "SluggedSendableSerializer"
    CONTENT_SINGLE_TEMPLATE = "Hello {}!"
    CONTENT_MULTIPLE = "To multiple recipients"

    @cached_property
    def slugged_serializer_class(self) -> str:
        try:
            return super()._slugged_serializer_class
        except AttributeError:
            return self._slugged_serializer_class

    @cached_property
    def CONTENT_SINGLE(self) -> str:
        return self.CONTENT_SINGLE_TEMPLATE.format(self.user.username)

    def setUp(self) -> None:
        super().setUp()

        sendable = self.create_sendable(self.CONTENT_SINGLE)
        self.add_to_recipients(sendable)

        other_sendable = self.create_sendable(self.CONTENT_MULTIPLE)
        for recipient in self.user, self.other_user:
            self.add_to_recipients(other_sendable, recipient)

    def create_sendable(self, content: str, **extra_kwargs: str) -> Sendable:
        kwargs = {"content": content, **extra_kwargs}
        if self.entity_name == "message":
            kwargs["sender"] = self.sender

        sendable_class = (
            self.slugged_sendable_class if extra_kwargs else self.sendable_class
        )
        return cast(Sendable, sendable_class.objects.create(**kwargs))

    def add_to_recipients(
        self, sendable: SendableAbstract, user: Any = None, is_read: bool | None = None
    ) -> None:
        if user is None:
            user = self.user
        if is_read is None:
            is_read = self.is_read

        ReceivedSendable.objects.create(
            recipient=user, sendable=sendable, is_read=is_read
        )
        RecipientSendableAssociation.objects.create(recipient=user, sendable=sendable)

    def send_sendable(self, content: str, is_read: bool | None = None) -> None:
        sendable = self.create_sendable(content)
        self.add_to_recipients(sendable, is_read=is_read)

    def get_expected_data(self, data: dict[str, Any]) -> dict[str, Any]:
        expected_data = {"is_read": self.is_read, **data}

        if self.entity_name == "message":
            expected_data["sender"] = {
                "id": self.sender.id,
                "username": self.sender.username,
            }

        return expected_data

    def check_id_and_sent_on(self, data: dict[str, Any]) -> None:
        id = data.pop("id")
        self.assertIsInstance(id, int)
        self.assertGreater(id, 0)

        sent_on = data.pop("sent_on")
        sent_on_datetime = parse_datetime(sent_on)
        self.assertIsInstance(sent_on_datetime, datetime)


class SendableMixin(TestMixin):
    entity_name = "sendable"
    sendable_class = Sendable
    slugged_sendable_class = SluggedSendable


class MessageMixin(TestMixin):
    entity_name = "message"
    sendable_class = Message
    slugged_sendable_class = SluggedMessage
    _slugged_serializer_class = "SluggedMessageSerializer"

    def setUp(self) -> None:
        super().setUp()
        self.sender = User.objects.create_user(username="mike")


class NoticeMixin(TestMixin):
    entity_name = "notice"
    sendable_class = Notice
    slugged_sendable_class = SluggedNotice

    def setUp(self) -> None:
        self.user = User.objects.create_superuser(username="bob")
        self.other_user = User.objects.create_user(username="alice")

        self.client.force_authenticate(self.user)


class TestSentMixin(TestCaseType):
    def setUp(self) -> None:
        super().setUp()
        self.client.force_authenticate(self.sender)

    def get_expected_data(self, data: dict[str, Any]) -> dict[str, Any]:
        sendable_class = app_settings[self.entity_name].SENDABLE_CLASS
        sendable = cast(
            Sendable, sendable_class.objects.filter(content=data["content"]).first()
        )

        content_type = ContentType.objects.get_for_model(sendable_class)

        associations = RecipientSendableAssociation.objects.filter(
            object_id=sendable.id, content_type=content_type
        ).prefetch_related("recipient")

        recipients = [
            {"id": association.recipient.id, "username": association.recipient.username}
            for association in associations
        ]

        return {"recipients": recipients, **data}


class SluggedSendableSerializer(ReceivedSendableSerializer):
    slug = serializers.SlugField(source="sendable.slug")


class SluggedMessageSerializer(MessageDetailSerializer):
    slug = serializers.SlugField(source="sendable.slug")


class SluggedMessageSentSerializer(MessageSentSerializer):
    slug = serializers.SlugField(source="sendable.slug")


class assert_forbidden:
    def __init__(self, function: Callable) -> None:
        self.function = function

    def decorated(self, instance: Any) -> Any:
        instance.client.handler._force_user = None
        instance.client.handler._force_token = None

        response = self.function(instance)
        instance.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        instance.client.force_authenticate(instance.user)

    def __get__(self, instance: Any, owner: type) -> Any:
        return partial(self.decorated, instance)


def with_setting_changed(key: str, value: Any) -> Callable:
    class Descriptor:
        def __init__(self, function: Callable) -> None:
            self.function = function

        def __call__(self, instance: Any, *args: Any, **kwargs: Any) -> Any:
            with instance.setting_changed(key, value):
                return self.function(instance, *args, **kwargs)

        def __get__(self, instance: Any, owner: type) -> Any:
            return partial(self.__call__, instance)

    return Descriptor
