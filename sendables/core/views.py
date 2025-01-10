from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from rest_framework import exceptions, generics, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response

from sendables.core.mixins import (
    ContextMixin,
    FilterMixin,
    PaginatedMixin,
    RetrieveReceivedMixin,
)
from sendables.core.models import ReceivedSendable, RecipientSendableAssociation
from sendables.core.serializers import (
    DeleteSentSerializer,
    DeleteSerializer,
    MarkSerializer,
)

User = get_user_model()


class SendView(ContextMixin, generics.CreateAPIView):
    def get_serializer_class(self) -> type[serializers.Serializer]:
        return self.entity_settings.SEND_SERIALIZER_CLASS


class MarkAsReadView(ContextMixin, generics.GenericAPIView):
    serializer_class = MarkSerializer
    is_read = True

    def patch(self, request: Request, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.mark(is_read=self.is_read)  # type: ignore[attr-defined]

        return Response()


class MarkAsUnreadView(MarkAsReadView):
    is_read = False


class DeleteView(ContextMixin, generics.GenericAPIView):
    serializer_class: type[serializers.Serializer] = DeleteSerializer

    def delete(self, request: Request, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()  # type: ignore[attr-defined]

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteSentView(DeleteView):
    serializer_class = DeleteSentSerializer


class ListView(PaginatedMixin, RetrieveReceivedMixin, generics.ListAPIView):
    def get_serializer_class(self) -> type[serializers.Serializer]:
        return self.entity_settings.LIST_SERIALIZER_CLASS


class ListReadView(ListView):
    filters = {"is_read": True}


class ListUnreadView(ListView):
    filters = {"is_read": False}


class ListSentView(PaginatedMixin, ContextMixin, FilterMixin, generics.ListAPIView):
    def get_queryset(self) -> QuerySet:
        """Fetch recipient-sendable association records of sendables
        sent by current user.
        """
        Sendable = self.entity_settings.SENDABLE_CLASS

        if not hasattr(Sendable, "sender"):
            raise exceptions.NotFound

        content_type = ContentType.objects.get_for_model(Sendable)

        # 1. Since there is no guarantee the sendable Model has a GenericRelation,
        # `sendable__sender` on RecipientSendableAssociation cannot be queried. Fetch
        # ids of user's sent sendables first, then get their respective associations
        # along with recipients and sendables.
        sendables = Sendable.objects.filter(sender=self.request.user, is_removed=False)
        sendable_ids = self.get_filtered_ids(sendables)

        filter_recipients_function = self.entity_settings.FILTER_RECIPIENTS
        search_recipients_filters = self.get_search_filters(
            "recipient", User.objects.all(), filter_recipients_function
        )

        # 2. Get sendables of queried recipients.
        sendables_with_recipients_ids = RecipientSendableAssociation.objects.filter(
            content_type=content_type, **search_recipients_filters
        ).values("object_id")

        # 3. End up with sendables passing both the "sendable" filters and the
        # "recipient" filters.
        eligible_sendable_ids = sendable_ids.intersection(sendables_with_recipients_ids)

        # Avoid using `search_recipients_filters` here, and do it at step 2. to include
        # even association records that (unlike their "siblings") fail the "recipient"
        # filters, but are needed to compose the full data.
        results = RecipientSendableAssociation.objects.filter(
            object_id__in=eligible_sendable_ids,
            content_type=content_type,
        ).prefetch_related("recipient", "sendable")

        # Do the sorting in Python, as explained in the comment of
        # `mixins.RetrieveReceivedMixin.get_queryset`.
        return cast(QuerySet, sorted(results, key=self.entity_settings.SORT_SENT_KEY))

    def get_serializer_class(self) -> type[serializers.Serializer]:
        return self.entity_settings.LIST_SENT_SERIALIZER_CLASS


class DetailView(ContextMixin, generics.RetrieveAPIView):
    def get_queryset(self) -> QuerySet:
        # Setup `lookup_field` for `get_object()` to use.
        self.lookup_field = self.entity_settings.SENDABLE_KEY_NAME

        Sendable = self.entity_settings.SENDABLE_CLASS

        content_type = ContentType.objects.get_for_model(Sendable)
        prefetch_fields = self.entity_settings.GET_RECEIVED_PREFETCH_FIELDS(Sendable)

        return ReceivedSendable.objects.filter(
            recipient=self.request.user,
            content_type=content_type,
        ).prefetch_related(*prefetch_fields)

    def get_serializer_class(self) -> type[serializers.Serializer]:
        return self.entity_settings.DETAIL_SERIALIZER_CLASS


class DetailSentView(ContextMixin, generics.ListAPIView):
    def get_queryset(self) -> QuerySet:
        """Get QuerySet with single sendable, chosen by URL argument."""
        Sendable = self.entity_settings.SENDABLE_CLASS

        if not hasattr(Sendable, "sender"):
            raise exceptions.NotFound

        key_name = self.entity_settings.SENDABLE_KEY_NAME
        unique_key_filter = {key_name: self.kwargs[key_name]}

        sendable_ids = Sendable.objects.filter(
            sender=self.request.user, is_removed=False, **unique_key_filter
        ).values("id")

        content_type = ContentType.objects.get_for_model(Sendable)

        return RecipientSendableAssociation.objects.filter(
            object_id__in=sendable_ids,
            content_type=content_type,
        ).prefetch_related("recipient", "sendable")

    def get_serializer_class(self) -> type[serializers.Serializer]:
        return self.entity_settings.DETAIL_SENT_SERIALIZER_CLASS
