Settings
========

All the settings of *drf-sendables* have default values, which can be overriden. This is done by defining a
``SENDABLES`` `dict` in your Django project's settings file. Then, for each *entity* you want to configure, use its
name as the key, and, as the value, a `dict` with any of the keys mentioned below. For example:

.. code-block:: python

   SENDABLES = {
       "message": {
           "PARTICIPANT_KEY_NAME": "username",
           "PARTICIPANT_KEY_TYPE": "rest_framework.serializers.CharField",
       },
       "notice": {
           "GET_VALID_ITEMS": "sendables.core.policies.select.get_valid_items_strict",
       },
   }

.. note::
   Settings described having an *object / dotted path* type, can either take an object (class/function) as a value, or a
   string containing a dotted import path to an object.

.. note::
   Every time you change settings related to the database, you should then generate and run database migrations.

Presented here are the settings for each *entity*, along with their type, default value, and description:

Sendables
---------

.. confval:: SEND_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.core.serializers.SendSerializer`

   Serializer for creating and dispatching sendables to recipients.

.. confval:: ALLOW_SEND_TO_SELF
   :type: :class:`bool` */ object / dotted path*
   :default: ``False``

   Whether a user is considered a valid recipient of their own sendables. Can be a `bool`, or a callable accepting a single
   `request` argument.

.. confval:: SENT_FIELD_NAMES
   :type: :class:`list`\[:class:`str`]
   :default: ``["content"]``

   The fields of sendable model/serializer to be used during sending. They must be present on the used sendable model, and on
   the sendable detail serializer with ``source="sendable.field_name"``.

.. confval:: PARTICIPANT_KEY_NAME
   :type: :class:`str`
   :default: ``"id"``

   Name of field uniquely identifying users, used for recipient selection during sending, and sender serializer representation.

.. confval:: PARTICIPANT_KEY_TYPE
   :type: *object / dotted path*
   :default: ``"rest_framework.serializers.IntegerField"``

   Serializer field type of field uniquely identifying users, used for recipient selection during sending, and sender serializer
   representation.

.. confval:: GET_VALID_RECIPIENTS
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.send.get_valid_recipients_lenient`

   Method of choosing valid recipients during sending. Takes 3 arguments: 1) The `request` object, 2) a `list` of `strings` containing
   values of a field (e.g. `id`) that uniquely identifies users that the client requested to use as recipients, and 3) the "send"
   action's serializer instance. Should return a `QuerySet` of users deemed as valid recipients.

.. confval:: SENDABLE_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.core.models.Sendable`

   The sendable Django model class to be used.

.. confval:: SENDABLE_KEY_NAME
   :type: :class:`str`
   :default: ``"id"``

   Name of field uniquely identifying sendables, used for sendable selection during sending, and URL argument naming.

.. confval:: SENDABLE_KEY_TYPE
   :type: *object / dotted path*
   :default: ``"rest_framework.serializers.IntegerField"``

   Serializer field type of field uniquely identifying sendables, used for sendable selection during sending, and
   URL argument typing.

.. confval:: GET_VALID_ITEMS
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.select.get_valid_items_lenient`

   Method of choosing valid items (sendables/received sendables) during selecting. Takes 5 arguments: 1) The `request`
   object, 2) a `list` of `strings` containing values of a field (e.g. `id`) that uniquely identifies items that the client
   requested to select, 3) the "select" action's serializer instance, 4) the item's model class, and 5) a `string` indicating
   the user's relation to the items (``"sender"``/``"recipient"``). It can also take an ``is_removed=False`` argument, in the
   case of selecting sent sendables for deletion. Should return a `QuerySet` of items deemed as validly selected.

.. confval:: LIST_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.core.serializers.ReceivedSendableSerializer`

   Serializer to represent received sendables during list view.

.. confval:: DETAIL_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.core.serializers.ReceivedSendableSerializer`

   Serializer to represent a received sendable during detail view.

.. confval:: SORT_RECEIVED_KEY
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.list.sort_received_key`

   Sorting key for received sendables. Function that gets passed as `key` to :func:`sorted` during received sendable list view.
   Takes a :class:`~sendables.core.models.ReceivedSendable` object as argument.

.. confval:: SORT_SENT_KEY
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.list.sort_sent_key`

   Sorting key for recipient-sendable associations. Function that gets passed as `key` to :func:`sorted` during sent sendable list
   view. Takes a :class:`~sendables.core.models.RecipientSendableAssociation` object as argument.

.. confval:: FILTER_SENDABLES
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.filter.filter_sendables`

   Function to filter listed sendables, using the respective URL query parameters. A list-type view's :confval:`specific setting <LIST_VIEW_NAME_FILTER_SENDABLES>`
   overrides this. Takes 3 arguments: 1) The `request` object, 2) a `QuerySet` of :class:`~sendables.core.models.Sendable` objects, and 3) a `dict` of
   the entity settings. Should return the filtered sendables `QuerySet`.

.. confval:: FILTER_RECIPIENTS
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.filter.filter_recipients`

   Function to filter listed sendables by their recipients, using the respective URL query parameters. Takes 3 arguments: 1) The
   `request` object, 2) a `QuerySet` of `User` objects, and 3) a `dict` of the entity settings. Should return the filtered users
   `QuerySet`.

.. confval:: FILTER_FIELDS_SENDABLES
   :type: :class:`dict`\[:class:`str`, :class:`~sendables.core.types.FilterType`]
   :default: ``{"content": FilterType.CONTAINS, "sent_on": FilterType.DATETIME, "sender__id": FilterType.EQUALS, "sender__username": FilterType.EQUALS}``

   Sendable fields to `FilterType` mapping, used for searching.

.. confval:: FILTER_FIELDS_RECIPIENTS
   :type: :class:`dict`\[:class:`str`, :class:`~sendables.core.types.FilterType`]
   :default: ``{"id": FilterType.EQUALS, "username": FilterType.EQUALS}``

   User fields to `FilterType` mapping, used for searching.

.. confval:: AFTER_SEND_CALLBACKS
   :type: :class:`list`\[*object / dotted path*]
   :default: ``[]``

   List of functions to be called after the sending of a sendable. They take 3 arguments: 1) The `request` object, 2) a `dict` of sent field names to
   their values (e.g. ``{"content": "hello"}``), and 3) the valid recipients as a `QuerySet` of `User` objects.

.. confval:: DELETE_HANGING_SENDABLES
   :type: :class:`bool`
   :default: ``True``

   Whether to delete database records not referenced by any other "alive" records. "Alive" here means not explicitly deleted by a user's actions.

.. confval:: GET_RECEIVED_PREFETCH_FIELDS
   :type: *object / dotted path*
   :default: :func:`sendables.core.policies.list.get_received_prefetch_fields`

   Function to provide "prefetch related" fields for received sendable list. Takes 1 argument: the sendable model class. Should return the model fields
   as a `list` of `string`\s.

.. confval:: PAGINATION_CLASS
   :type: *BasePagination / None*
   :default: ``None``

   `Pagination <https://www.django-rest-framework.org/api-guide/pagination/>`_ class to be used in list views. A list-type view's
   :confval:`specific setting <LIST_VIEW_NAME_PAGINATION_CLASS>` overrides this. Can be `None` for no pagination.

Given the following `view names`:

.. code-block::

   SEND
   MARK_AS_READ
   MARK_AS_UNREAD
   DELETE
   DELETE_SENT
   LIST
   LIST_READ
   LIST_UNREAD
   LIST_SENT
   DETAIL
   DETAIL_SENT

this kind of settings exist:

.. confval:: VIEW_NAME_PERMISSIONS
   :type: :class:`list`\[*object / dotted path*]
   :default: ``["rest_framework.permissions.IsAuthenticated"]``

   For example, `DELETE_PERMISSIONS`. List of `permission <https://www.django-rest-framework.org/api-guide/permissions/>`_ classes to be applied to
   the view indicated by `view name`.

Given the following `list view names`:

.. code-block::

   LIST
   LIST_READ
   LIST_UNREAD
   LIST_SENT

these kind of settings exist:

.. confval:: LIST_VIEW_NAME_FILTER_SENDABLES
   :type: *object / dotted path / None*
   :default: ``None``

   For example, `LIST_FILTER_SENDABLES`. Function to filter listed sendables, using the respective URL query parameters, in the view indicated by
   `list view name`. If not `None`, overrides the :confval:`generic setting <FILTER_SENDABLES>`. Takes 3 arguments: 1) The `request` object, 2) a
   `QuerySet` of :class:`~sendables.core.models.Sendable` objects, and 3) a `dict` of the entity settings. Should return the filtered sendables `QuerySet`.

.. confval:: LIST_VIEW_NAME_PAGINATION_CLASS
   :type: *BasePagination / None*
   :default: ``None``

   `Pagination <https://www.django-rest-framework.org/api-guide/pagination/>`_ class to be used in the view indicated by `list view name`. If not `None`,
   overrides the :confval:`generic setting <PAGINATION_CLASS>`.

Messages
--------

*Messages* use all the settings that :ref:`sendables <settings:Sendables>` do, plus some extra ones, while having different default values for some of
the settings.

.. confval:: SEND_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.SendMessageSerializer`
   :noindex:

   Serializer for creating and dispatching messages to recipients.

.. confval:: SENDABLE_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.models.Message`
   :noindex:

   The message Django model class to be used.

.. confval:: LIST_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.MessageListSerializer`
   :noindex:

   Serializer to represent received messages during list view.

.. confval:: LIST_SENT_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.MessageSentSerializer`

   Serializer to represent sent messages during list view.

.. confval:: DETAIL_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.MessageDetailSerializer`
   :noindex:

   Serializer to represent received messages during detail view.

.. confval:: DETAIL_SENT_SERIALIZER_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.MessageSentSerializer`

   Serializer to represent sent messages during detail view.

.. confval:: SENDER_FIELD_TYPE_LIST
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.ParticipantSerializer`

   Serializer/field to represent sender users during received message list view.

.. confval:: SENDER_FIELD_TYPE_DETAIL
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.ParticipantSerializer`

   Serializer/field to represent sender user during received message detail view.

.. confval:: RECIPIENT_FIELD_TYPE_LIST
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.ParticipantSerializer`

   Serializer/field to represent recipient users during sent message list view.

.. confval:: RECIPIENT_FIELD_TYPE_DETAIL
   :type: *object / dotted path*
   :default: :class:`sendables.messages.serializers.ParticipantSerializer`

   Serializer/field to represent recipient user during sent message detail view.

Notices
-------

*Notices* use all the settings that :ref:`sendables <settings:Sendables>` do, while having different default values for some of the settings.

.. confval:: SENDABLE_CLASS
   :type: *object / dotted path*
   :default: :class:`sendables.notices.models.Notice`
   :noindex:

   The notice Django model class to be used.

.. confval:: SEND_PERMISSIONS
   :type: :class:`list`\[*object / dotted path*]
   :default: ``["rest_framework.permissions.IsAdminUser"]``

   List of `permission <https://www.django-rest-framework.org/api-guide/permissions/>`_ classes to be applied to the
   :http:post:`send notice </notices/send/>` view.
