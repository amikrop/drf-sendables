from django.urls import URLResolver, include, path

from sendables.core import views
from sendables.core.settings import app_settings
from sendables.core.utils import check_direct_model_usage, get_url_arg_type


def sendables_path(route: str, entity_name: str = "sendable") -> URLResolver:
    """Generate and return the URL patterns for a sendable entity type.

    Use settings, generate URL pattern names, and choose URL argument types, based on
    given `entity_name`. Pass that name to all of the views. Make a non-abstract version
    of the sendable model that is used with those settings.

    Args:
        route: The URL path pattern
        entity_name: The name of the sendable entity type

    Returns:
        The URL patterns
    """
    entity_settings = app_settings[entity_name]

    check_direct_model_usage(entity_settings)

    detail_key_name = entity_settings.SENDABLE_KEY_NAME
    detail_key_type_internal = entity_settings.SENDABLE_KEY_TYPE
    detail_key_type = get_url_arg_type(detail_key_type_internal)

    return path(
        route,
        include(
            [
                path("send/", views.SendView.as_view(), name=f"{entity_name}-send"),
                path(
                    "mark-read/",
                    views.MarkAsReadView.as_view(),
                    name=f"{entity_name}-mark-read",
                ),
                path(
                    "mark-unread/",
                    views.MarkAsUnreadView.as_view(),
                    name=f"{entity_name}-mark-unread",
                ),
                path(
                    "delete/", views.DeleteView.as_view(), name=f"{entity_name}-delete"
                ),
                path(
                    "delete-sent/",
                    views.DeleteSentView.as_view(),
                    name=f"{entity_name}-delete-sent",
                ),
                path("", views.ListView.as_view(), name=f"{entity_name}-list"),
                path(
                    "read/",
                    views.ListReadView.as_view(),
                    name=f"{entity_name}-list-read",
                ),
                path(
                    "unread/",
                    views.ListUnreadView.as_view(),
                    name=f"{entity_name}-list-unread",
                ),
                path(
                    "sent/",
                    views.ListSentView.as_view(),
                    name=f"{entity_name}-list-sent",
                ),
                path(
                    f"<{detail_key_type}:{detail_key_name}>/",
                    views.DetailView.as_view(),
                    name=f"{entity_name}-detail",
                ),
                path(
                    f"sent/<{detail_key_type}:{detail_key_name}>/",
                    views.DetailSentView.as_view(),
                    name=f"{entity_name}-detail-sent",
                ),
            ]
        ),
        {"entity_name": entity_name},
    )
