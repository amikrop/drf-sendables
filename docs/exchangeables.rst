Exchangeables
=============

The following components can be used as parts of the system (most of them are already being used by default).
The :doc:`settings <settings>` page describes which of the following can be used at what places, and what are
the defaults. You can make your choices either among the ones listed here, or provide your own.

.. autoclass:: sendables.core.models.Sendable
   :show-inheritance:
   :members: content, is_removed, sent_on
   :undoc-members:

.. autoclass:: sendables.core.models.ReceivedSendable
   :show-inheritance:
   :members: is_read, recipient, content_type, object_id, sendable
   :undoc-members:

.. autoclass:: sendables.core.models.RecipientSendableAssociation
   :show-inheritance:
   :members: recipient, content_type, object_id, sendable
   :undoc-members:

.. autoclass:: sendables.messages.models.Message
   :show-inheritance:
   :members: content, is_removed, sent_on, sender
   :undoc-members:

.. autoclass:: sendables.notices.models.Notice
   :show-inheritance:
   :members: content, is_removed, sent_on
   :undoc-members:

.. autoclass:: sendables.core.serializers.ReceivedSendableSerializer
   :show-inheritance:

.. autoclass:: sendables.core.serializers.ContainerSerializer
   :show-inheritance:

.. autoclass:: sendables.core.serializers.SendSerializer
   :show-inheritance:
   :members:

.. autoclass:: sendables.messages.serializers.MessageListSerializer
   :show-inheritance:

.. autoclass:: sendables.messages.serializers.MessageDetailSerializer
   :show-inheritance:

.. autoclass:: sendables.messages.serializers.MessageSentSerializer
   :show-inheritance:

.. autoclass:: sendables.messages.serializers.SendMessageSerializer
   :show-inheritance:
   :members:

.. autoclass:: sendables.messages.serializers.ParticipantSerializer
   :show-inheritance:

.. autoclass:: sendables.core.types.FilterType
   :show-inheritance:
   :members:

.. autofunction:: sendables.core.policies.filter.filter_sendables

.. autofunction:: sendables.core.policies.filter.filter_recipients

.. autofunction:: sendables.core.policies.list.get_received_prefetch_fields

.. autofunction:: sendables.core.policies.list.sort_received_key

.. autofunction:: sendables.core.policies.list.sort_sent_key

.. autofunction:: sendables.core.policies.select.get_valid_items_lenient

.. autofunction:: sendables.core.policies.select.get_valid_items_strict

.. autofunction:: sendables.core.policies.send.get_valid_recipients_lenient

.. autofunction:: sendables.core.policies.send.get_valid_recipients_strict

.. autofunction:: sendables.core.urls.sendables_path
