import re
from typing import Any, Callable, cast

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from rest_framework.pagination import BasePagination
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from sendables.core.models import ReceivedSendable
from sendables.core.settings import Settings, app_settings
from sendables.core.types import Configured, GenericViewProtocol


class PermissionsMixin(GenericViewProtocol):
    """Applies appropriate view permissions."""

    def get_view_setting(self, setting_type: str) -> Any:
        """Get setting of given kind, regarding the current view."""
        # Construct setting key out of view class name.
        class_name = self.__class__.__name__
        parts = re.findall("[A-Z][a-z]*", class_name)[:-1]
        name_upper = "_".join(part.upper() for part in parts)

        setting_key = f"{name_upper}_{setting_type}"

        return getattr(self.entity_settings, setting_key)

    def get_permissions(self) -> list[BasePermission]:
        # Make shortcuts for entity info here, as `get_permissions()` is called early.
        self.entity_name = self.kwargs.get("entity_name", "sendable")
        self.entity_settings = app_settings[self.entity_name]

        permission_classes = self.get_view_setting("PERMISSIONS")
        return [permission() for permission in permission_classes]


class ContextMixin(PermissionsMixin):
    """Provides the entity name to serializers."""

    def get_serializer_context(self) -> dict[str, Any]:
        context = super().get_serializer_context()  # type: ignore[safe-super]
        context["entity_name"] = self.entity_name

        return context


class FilterMixin(Configured):
    def get_filtered_ids(
        self,
        queryset: QuerySet,
        filter_function: (
            Callable[[Request, QuerySet, Settings], QuerySet] | None
        ) = None,
    ) -> QuerySet:
        """Apply appropriate filter function to given QuerySet and return the resulting
        id values.
        """
        if filter_function is None:
            filter_function = (
                self.get_view_setting("FILTER_SENDABLES")
                or self.entity_settings.FILTER_SENDABLES
            )
        if filter_function is not None:
            queryset = filter_function(
                self.request,  # type: ignore[attr-defined]
                queryset,
                self.entity_settings,
            )
        return cast(QuerySet, queryset.values("id"))

    def get_search_filters(
        self,
        foreign_key_name: str,
        queryset: QuerySet,
        filter_function: (
            Callable[[Request, QuerySet, Settings], QuerySet] | None
        ) = None,
    ) -> dict[str, QuerySet]:
        """Return "foreign key in" lookup dict, if applied filters narrow down the given
        QuerySet. If it remains intact, return empty dict.
        """
        filtered_ids = self.get_filtered_ids(queryset, filter_function)

        if filtered_ids.query.where:
            return {f"{foreign_key_name}__in": filtered_ids}

        return {}


class RetrieveReceivedMixin(ContextMixin, FilterMixin):
    """Provides QuerySet of current user's received sendable references, along with
    their respective sendable records.
    """

    filters: dict[str, bool] = {}

    def get_queryset(self) -> QuerySet:
        Sendable = self.entity_settings.SENDABLE_CLASS

        search_sendables_filters = self.get_search_filters(
            "object_id", Sendable.objects.all()
        )
        content_type = ContentType.objects.get_for_model(Sendable)

        prefetch_fields = self.entity_settings.GET_RECEIVED_PREFETCH_FIELDS(Sendable)

        # With the sendable Model not being tied down/known beforehand, there is no
        # guarantee there is a GenericRelation on it, so .prefetch_related() cannot be
        # called with a Prefetch() of "sendable" and a QuerySet ordered by `sent_on` or
        # any other field. Therefore, do the sorting in Python.

        results = ReceivedSendable.objects.filter(
            recipient=self.request.user,  # type: ignore[attr-defined]
            content_type=content_type,
            **self.filters,
            **search_sendables_filters,
        ).prefetch_related(*prefetch_fields)

        return cast(
            QuerySet, sorted(results, key=self.entity_settings.SORT_RECEIVED_KEY)
        )


class PaginatedMixin(Configured):
    @property
    def paginator(self) -> BasePagination | None:
        """Try to get view-specific paginator, if not set fall back to generic
        paginator, if not set fall back to None.
        """
        if not hasattr(self, "_paginator"):
            if (
                view_pagination_class := self.get_view_setting("PAGINATION_CLASS")
            ) is None:
                if (
                    generic_pagination_class := self.entity_settings.PAGINATION_CLASS
                ) is None:
                    self._paginator = None
                else:
                    self._paginator = generic_pagination_class()
            else:
                self._paginator = view_pagination_class()

        return self._paginator
