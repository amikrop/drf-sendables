from rest_framework import status

from tests.models import Sendable
from tests.test_detail import MessageDetailTests
from tests.utils import TestSentMixin, with_setting_changed


class MessageDetailSentTests(TestSentMixin, MessageDetailTests):
    view_name_suffix = "-sent"

    def get_tested_record(self, sendable: Sendable) -> Sendable:
        return sendable

    def test_detail_sent_removed(self) -> None:
        sendable = self.sendable_class.objects.get(content=self.CONTENT_SINGLE)
        sendable.is_removed = True
        sendable.save()

        response = self.get(sendable.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @with_setting_changed("SENDABLE_CLASS", "tests.models.SluggedMessage")
    @with_setting_changed(
        "DETAIL_SENT_SERIALIZER_CLASS", "tests.utils.SluggedMessageSentSerializer"
    )
    def test_detail_custom_model_and_serializer(self) -> None:
        self.validate_slugged("Message text.", "message-text")
