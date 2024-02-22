from typing import TYPE_CHECKING, Any, Callable

from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase

from sendables.core.types import ManagedModel

if TYPE_CHECKING:

    class TestCaseType(APITestCase):
        entity_name: str
        sendable_class: type[ManagedModel]
        slugged_sendable_class: type[ManagedModel]
        _slugged_serializer_class: str
        url: str
        content_type: ContentType
        user: Any
        other_user: Any
        sender: Any
        setting_changed: Callable
        assert_bad_request: Callable
        assert_bad_request_with_content: Callable

else:

    class TestCaseType:
        pass
