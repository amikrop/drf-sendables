API
===

Intro
-----

By default, and if installed :ref:`as described <index:Installation>` on the front page, *drf-sendables* comes with two
*entities*: :ref:`messages <api:Messages>` and :ref:`notices <api:Notices>`.

The following specification refers to the default configuration, but most aspects, such as URL paths, request/response
data/format, field names, and searching mechanisms can be adjusted through :doc:`settings <settings>` and
:doc:`customized usage <custom>`.

Some endpoints, as shown below, accept URL query parameters, which are all optional, serving searching purposes.
The default search filters are of 3 types: *equals*, *contains*, and *datetime*. The first one requires equality between
the search term and the field value and the second one requires the search term being part (substring) of the field value.
The third search filter type supports `Django field lookups <https://docs.djangoproject.com/en/5.0/topics/db/queries/#field-lookups>`_
such as ``sent_on__gte=`` and requires `timestamps <https://en.wikipedia.org/wiki/Unix_time>`_ as values.

All non-URL request fields are required, and lists cannot be empty. Requests to any endpoint missing a field or having
an empty list-type field get responded with :http:statuscode:`400`.

According to default settings all requests must be authenticated, and :http:post:`send notice </notices/send/>` must be
made while authenticated as an administrator user. Requests lacking the required authentication get responded with
:http:statuscode:`403`.

Each endpoint only allows for a single HTTP method. If requested using any other, they respond with :http:statuscode:`405`.

The requests and responses can be of any content type that your Django REST Framework project is configured for
(either out of the box, or manually), but the following examples use *application/json*.

Endpoints
---------

You can find a summary of the endpoints at the :ref:`routing table <routingtable>`. Below is their detailed description:

Messages
~~~~~~~~

**Messages** are sent from a user to others. By default, apart from ``content`` and the :class:`other fields <sendables.core.models.Sendable>`,
they store "sender" information. Endpoints concerning messages require authenticated requests.

.. http:post:: /messages/send/
   :synopsis: Send a message to selected recipients

   Send a message to selected recipients

   **Example request**:

   .. sourcecode:: http

      POST /messages/send/ HTTP/1.1

      {
          "content": "Hello there",
          "recipient_ids": [
              5, 8, 26
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json

      {
          "content": "Hello there",
          "recipient_ids": [
              5, 8, 26
          ]
      }

   :<json string content: the message's content
   :<jsonarr integer recipient_ids: the recipient IDs
   :statuscode 201: Success

.. http:patch:: /messages/mark-read/
   :synopsis: Mark selected received messages as read

   Mark selected received messages as read

   **Example request**:

   .. sourcecode:: http

      PATCH /messages/mark-read/ HTTP/1.1

      {
          "message_ids": [
              34
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

   :<jsonarr integer message_ids: the IDs of received messages to be marked
   :statuscode 200: Success

.. http:patch:: /messages/mark-unread/
   :synopsis: Mark selected received messages as unread

   Mark selected received messages as unread

   **Example request**:

   .. sourcecode:: http

      PATCH /messages/mark-unread/ HTTP/1.1

      {
          "message_ids": [
              40, 41, 42
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

   :<jsonarr integer message_ids: the IDs of received messages to be marked
   :statuscode 200: Success

.. http:delete:: /messages/delete/
   :synopsis: Delete selected received messages

   Delete selected received messages

   **Example request**:

   .. sourcecode:: http

      DELETE /messages/delete/ HTTP/1.1

      {
          "message_ids": [
              11, 15
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content

   :<jsonarr integer message_ids: the IDs of received messages to be deleted
   :statuscode 204: Success

.. http:delete:: /messages/delete-sent/
   :synopsis: Delete selected sent messages

   Delete selected sent messages

   **Example request**:

   .. sourcecode:: http

      DELETE /messages/delete-sent/ HTTP/1.1

      {
          "message_ids": [
              9, 10, 18
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content

   :<jsonarr integer message_ids: the IDs of sent messages to be deleted
   :statuscode 204: Success

.. http:get:: /messages/
   :synopsis: List received messages

   List received messages

   **Example request**:

   .. sourcecode:: http

      GET /messages/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Greetings",
              "id": 3,
              "is_read": false,
              "sender": {
                  "id": 14,
                  "username": "john"
              },
              "sent_on": "2024-02-15T17:26:30.780074Z"
          },
          {
              "content": "Lorem ipsum",
              "id": 2,
              "is_read": true,
              "sender": {
                  "id": 22,
                  "username": "helen"
              },
              "sent_on": "2024-02-14T10:01:42.523326Z"
          }
      ]

   :query contains content: message content
   :query datetime sent_on: message "sent on"
   :query equals sender__id: sender ID
   :query equals sender__username: sender username
   :statuscode 200: Success

.. http:get:: /messages/read/
   :synopsis: List read received messages

   List read received messages

   **Example request**:

   .. sourcecode:: http

      GET /messages/read/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Congratulations",
              "id": 6,
              "is_read": true,
              "sender": {
                  "id": 31,
                  "username": "nick"
              },
              "sent_on": "2024-02-16T09:30:47.290671Z"
          },
          {
              "content": "Lorem ipsum",
              "id": 2,
              "is_read": true,
              "sender": {
                  "id": 22,
                  "username": "helen"
              },
              "sent_on": "2024-02-14T10:01:42.523326Z"
          }
      ]

   :query contains content: message content
   :query datetime sent_on: message "sent on"
   :query equals sender__id: sender ID
   :query equals sender__username: sender username
   :statuscode 200: Success

.. http:get:: /messages/unread/
   :synopsis: List unread received messages

   List unread received messages

   **Example request**:

   .. sourcecode:: http

      GET /messages/unread/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Have a nice day",
              "id": 15,
              "is_read": false,
              "sender": {
                  "id": 23,
                  "username": "paul"
              },
              "sent_on": "2024-02-17T19:11:01.281093Z"
          },
          {
              "content": "Greetings",
              "id": 3,
              "is_read": false,
              "sender": {
                  "id": 14,
                  "username": "john"
              },
              "sent_on": "2024-02-15T17:26:30.780074Z"
          }
      ]

   :query contains content: message content
   :query datetime sent_on: message "sent on"
   :query equals sender__id: sender ID
   :query equals sender__username: sender username
   :statuscode 200: Success

.. http:get:: /messages/sent/
   :synopsis: List sent messages

   List sent messages

   **Example request**:

   .. sourcecode:: http

      GET /messages/sent/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Hello, people",
              "id": 37,
              "recipients": [
                  {
                      "id": 72,
                      "username": "jenny"
                  },
                  {
                      "id": 89,
                      "username": "chris"
                  }
               ],
               "sent_on": "2024-03-22T12:29:10.265971Z"
          },
          {
              "content": "Happy birthday",
              "id": 35,
              "recipients": [
                  {
                      "id": 55,
                      "username": "luke"
                  }
               ],
               "sent_on": "2024-03-20T18:40:32.965873Z"
          }
      ]

   :query contains content: message content
   :query datetime sent_on: message "sent on"
   :query equals sender__id: sender ID
   :query equals sender__username: sender username
   :query equals recipient_id: recipient ID
   :query equals recipient_username: recipient username
   :statuscode 200: Success

.. http:get:: /messages/(int:message_id)/
   :synopsis: Received message detail

   Received message detail

   **Example request**:

   .. sourcecode:: http

      GET /messages/3/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "content": "Greetings",
          "id": 3,
          "is_read": false,
          "sender": {
              "id": 14,
              "username": "john"
          },
          "sent_on": "2024-02-15T17:26:30.780074Z"
      }

   :statuscode 200: Success
   :statuscode 404: Queried ID not belonging to any received message of the user

.. http:get:: /messages/sent/(int:message_id)/
   :synopsis: Sent message detail

   Sent message detail

   **Example request**:

   .. sourcecode:: http

      GET /messages/sent/37/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "content": "Hello, people",
          "id": 37,
          "recipients": [
              {
                  "id": 72,
                  "username": "jenny"
              },
              {
                  "id": 89,
                  "username": "chris"
              }
          ],
          "sent_on": "2024-03-22T12:29:10.265971Z"
      }

   :statuscode 200: Success
   :statuscode 404: Queried ID not belonging to any sent message of the user

Notices
~~~~~~~

**Notices** are sent from "the system" to users. They don't have a specific sender, and can only be sent from
administrator users. Thus, sending notices requires being authenticated as an administrator user, and the rest of
their endpoints require authenticated requests.

.. http:post:: /notices/send/
   :synopsis: Send a notice to selected recipients

   Send a notice to selected recipients

   **Example request**:

   .. sourcecode:: http

      POST /notices/send/ HTTP/1.1

      {
          "content": "Maintenance coming up",
          "recipient_ids": [
              7, 22, 27, 45
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 201 Created
      Content-Type: application/json

      {
          "content": "Maintenance coming up",
          "recipient_ids": [
              7, 22, 27, 45
          ]
      }

   :<json string content: the notice's content
   :<jsonarr integer recipient_ids: The recipient IDs
   :statuscode 201: Success

.. http:patch:: /notices/mark-read/
   :synopsis: Mark selected received notices as read

   Mark selected received notices as read

   **Example request**:

   .. sourcecode:: http

      PATCH /notices/mark-read/ HTTP/1.1

      {
          "notice_ids": [
              19, 28
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

   :<jsonarr integer notice_ids: the IDs of received notices to be marked
   :statuscode 200: Success

.. http:patch:: /notices/mark-unread/
   :synopsis: Mark selected received notices as unread

   Mark selected received notices as unread

   **Example request**:

   .. sourcecode:: http

      PATCH /notices/mark-unread/ HTTP/1.1

      {
          "notice_ids": [
              2
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK

   :<jsonarr integer notice_ids: the IDs of received notices to be marked
   :statuscode 200: Success

.. http:delete:: /notices/delete/
   :synopsis: Delete selected received notices

   Delete selected received notices

   **Example request**:

   .. sourcecode:: http

      DELETE /notices/delete/ HTTP/1.1

      {
          "notice_ids": [
              11, 15, 47
          ]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 204 No Content

   :<jsonarr integer notice_ids: the IDs of received notices to be deleted
   :statuscode 204: Success

.. http:get:: /notices/
   :synopsis: List received notices

   List received notices

   **Example request**:

   .. sourcecode:: http

      GET /notices/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Feel free to ask us anything",
              "id": 4,
              "is_read": false,
              "sent_on": "2024-01-02T20:01:31.281094Z"
          },
          {
              "content": "Welcome",
              "id": 3,
              "is_read": true,
              "sent_on": "2024-01-02T19:55:03.123811Z"
          }
      ]

   :query contains content: notice content
   :query datetime sent_on: notice "sent on"
   :statuscode 200: Success

.. http:get:: /notices/read/
   :synopsis: List read received notices

   List read received notices

   **Example request**:

   .. sourcecode:: http

      GET /notices/read/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Check out this new feature",
              "id": 7,
              "is_read": true,
              "sent_on": "2024-01-04T09:56:38.100680Z"
          },
          {
              "content": "Welcome",
              "id": 3,
              "is_read": true,
              "sent_on": "2024-01-02T19:55:03.123811Z"
          }
      ]

   :query contains content: notice content
   :query datetime sent_on: notice "sent on"
   :statuscode 200: Success

.. http:get:: /notices/unread/
   :synopsis: List unread received notices

   List unread received notices

   **Example request**:

   .. sourcecode:: http

      GET /notices/unread/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      [
          {
              "content": "Special offer",
              "id": 10,
              "is_read": false,
              "sent_on": "2024-01-09T21:12:11.101032Z"
          },
          {
              "content": "Feel free to ask us anything",
              "id": 4,
              "is_read": false,
              "sent_on": "2024-01-02T20:01:31.281094Z"
          }
      ]

   :query contains content: notice content
   :query datetime sent_on: notice "sent on"
   :statuscode 200: Success

.. http:get:: /notices/(int:notice_id)/
   :synopsis: Received notice detail

   Received notice detail

   **Example request**:

   .. sourcecode:: http

      GET /notices/7/ HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
          "content": "Check out this new feature",
          "id": 7,
          "is_read": true,
          "sent_on": "2024-01-04T09:56:38.100680Z"
      }

   :statuscode 200: Success
   :statuscode 404: Queried ID not belonging to any received notice of the user
