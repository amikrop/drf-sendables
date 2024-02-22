from sendables.core.urls import sendables_path

urlpatterns = [
    sendables_path("sendables/"),
    sendables_path("messages/", "message"),
    sendables_path("notices/", "notice"),
]
