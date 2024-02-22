Customized usage
================

:ref:`Installing <index:Installation>` the `sendables` Django app and using ``include("sendables.urls")`` mounts the `messages` and `notices`
URLs on `messages/` and `notices/` respectively (relative to the path you called the `include` on). If you want to only use one of those two
*entities* (and their URLs), and/or mount them on different sub-paths, you can explicitly include their respective sub-package's URLs instead:

.. code-block:: python

   urlpatterns = [
       # ...
       path("user-messages/", include("sendables.messages.urls")),
   ]

The above only mounts the `messages` URLs on `user-messages/`.

Everything else stays the same: You still add ``"sendables"`` to your ``INSTALLED_APPS`` and still run ``python manage.py makemigrations sendables``
and ``python manage.py makemigrations sendables`` afterwards.

This will only cause the database table for the :class:`~sendables.messages.models.Message` model to be created (plus
:class:`~sendables.core.models.ReceivedSendable` and :class:`~sendables.core.models.RecipientSendableAssociation` which are used for all entity types).

**Messages** and **notices** are two `entities` based on a more generic `entity`: **sendable**.

If you want a vanilla entity type (which you will probably want to configure), you can instead call :func:`~sendables.core.urls.sendables_path`
with a URL path as a first argument, and an `entity` name as an optional second argument (default is ``"sendable"``). You can call this function as many times
as you want (with different/unique URL paths and entity names):

.. code-block:: python

   urlpatterns = [
       # ...
       sendables_path("personal-messages/"),
       sendables_path("alerts/", "alert"),
       sendables_path("communication/", "deliverable"),
   ]

You can then :doc:`configure <settings>` each `entity` using its entity name (in the above example: ``"sendable"``, ``"alert"``, and ``"deliverable"``).

Any of the three builtin sendable models, :class:`~sendables.core.models.Sendable`, :class:`~sendables.messages.models.Message`, and :class:`~sendables.notices.models.Notice`,
is abstract by default, unless declared as the :confval:`SENDABLE_CLASS` of an entity mounted through :func:`~sendables.core.urls.sendables_path`. This prevents the
unnecessary creation of database tables not meant to be used.

To properly use any of those three models in the Django interactive shell (``$ python manage.py shell``) requires their respective call of :func:`~sendables.core.urls.sendables_path`.
This marks the `entity` model as "concrete" (non-abstract). The easiest way to do this is importing your project's URLs module:

.. code-block:: pycon

   $ python manage.py shell
   >>> import myproject.urls

Then, you can use the models as normal:

.. code-block:: pycon

   >>> from sendables.core.models import Sendable
   >>> Sendable.objects.all()
