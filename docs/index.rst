drf-sendables
=============

User messages for Django REST Framework
---------------------------------------

*drf-sendables* is a `Django <https://www.djangoproject.com/>`_ reusable app providing the backend
for dispatching and managing in-site message-like entities. It can be plugged into a Django project,
utilizing any existing user authentication system. The HTTP REST API is implemented using
`Django REST framework <https://www.django-rest-framework.org/>`_.

Installation
------------

The following versions are supported:

    - Python: 3.10, 3.11
    - Django: 3.0 - 5.0
    - Django REST Framework: 3.10 - 3.14

- Install via `pip <https://packaging.python.org/tutorials/installing-packages/>`_:

.. code-block:: bash

   $ pip install drf-sendables

- Add it to your ``INSTALLED_APPS``:

.. code-block:: python

   INSTALLED_APPS = [
       # ...
       "sendables",
   ]

- Register the app's URLs under a path of your choice:

.. code-block:: python

   urlpatterns = [
       # ...
       path("some-path/", include("sendables.urls")),
   ]

where ``"some-path/"`` could be any URL.

- Optionally, configure the app :doc:`settings <settings>`.

- Generate and run the database migrations:

.. code-block:: bash

   $ python manage.py makemigrations sendables
   $ python manage.py migrate

Usage
-----

You may want to consult the description of the app's :ref:`endpoints <api:endpoints>`. For customized usage,
see the relevant :doc:`page <custom>`.

License
-------

Distributed under the `MIT License <https://github.com/amikrop/drf-sendables/blob/master/LICENSE>`_.

.. toctree::
   :maxdepth: 1
   :caption: Contents
   :hidden:

   api
   settings
   custom
   exchangeables
