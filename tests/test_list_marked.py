from django.urls import reverse
from rest_framework.test import APITestCase

from tests.test_list import ListTests
from tests.utils import MessageMixin, NoticeMixin, SendableMixin


class ListUnreadTests(ListTests):
    list_type = "LIST_UNREAD"

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        state = "read" if cls.is_read else "unread"
        cls.url = reverse(f"{cls.entity_name}-list-{state}")

    def setUp(self) -> None:
        super().setUp()

        for _ in range(2):
            self.send_sendable(self.CONTENT_SINGLE, is_read=not self.is_read)


class ListReadTests(ListUnreadTests):
    list_type = "LIST_READ"
    is_read = True


class SendableListUnreadTests(ListUnreadTests, SendableMixin, APITestCase):
    pass


class SendableListReadTests(ListReadTests, SendableMixin, APITestCase):
    pass


class MessageListUnreadTests(ListUnreadTests, MessageMixin, APITestCase):
    pass


class MessageListReadTests(ListReadTests, MessageMixin, APITestCase):
    pass


class NoticeListUnreadTests(ListUnreadTests, NoticeMixin, APITestCase):
    pass


class NoticeListReadTests(ListReadTests, NoticeMixin, APITestCase):
    pass
