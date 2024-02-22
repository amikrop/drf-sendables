drf-sendables
=============

User messages for Django REST Framework
---------------------------------------

.. image:: https://img.shields.io/pypi/v/drf-sendables.svg
   :target: https://pypi.org/project/drf-sendables/
   :alt: PyPI

.. image:: https://img.shields.io/pypi/l/drf-sendables.svg
   :target: https://pypi.org/project/drf-sendables/
   :alt: PyPI - License

.. image:: https://img.shields.io/pypi/pyversions/drf-sendables.svg
   :target: https://pypi.org/project/drf-sendables/
   :alt: PyPI - Python Version

.. image:: https://codecov.io/gh/amikrop/drf-sendables/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/amikrop/drf-sendables
   :alt: Coverage

.. image:: https://readthedocs.org/projects/drf-sendables/badge/?version=latest
   :target: https://drf-sendables.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

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

- Optionally, configure the app `settings <https://drf-sendables.readthedocs.io/en/latest/settings.html>`_.

- Generate and run the database migrations:

.. code-block:: bash

   $ python manage.py makemigrations sendables
   $ python manage.py migrate

Usage
-----

You can find the description of the app's `endpoints <https://drf-sendables.readthedocs.io/en/latest/endpoints.html>`_
in the `documentation <https://drf-sendables.readthedocs.io/en/latest/>`_. For customized usage, see the relevant
`page <https://drf-sendables.readthedocs.io/en/latest/custom.html>`_.

License
-------

Distributed under the `MIT License <https://github.com/amikrop/drf-sendables/blob/master/LICENSE>`_.
