from django.urls import include, path

urlpatterns = [
    path("messages/", include("sendables.messages.urls")),
    path("notices/", include("sendables.notices.urls")),
]
