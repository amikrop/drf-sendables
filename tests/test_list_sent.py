from tests.test_list import MessageListTests
from tests.utils import TestSentMixin, with_setting_changed


class MessageListSentTests(TestSentMixin, MessageListTests):
    action = "list-sent"
    list_type = "LIST_SENT"
    sort_key = "SORT_SENT_KEY"

    def test_list_sent_removed(self) -> None:
        sendable = self.sendable_class.objects.get(content=self.CONTENT_SINGLE)
        sendable.is_removed = True
        sendable.save()

        response = self.get()
        self.assert_contents_in(response, self.CONTENT_MULTIPLE)

    @with_setting_changed("SENDABLE_CLASS", "tests.models.SluggedMessage")
    @with_setting_changed(
        "LIST_SENT_SERIALIZER_CLASS", "tests.utils.SluggedMessageSentSerializer"
    )
    def test_list_custom_model_and_serializer(self) -> None:
        self.validate_slugged("Message {}!", "message{}")
