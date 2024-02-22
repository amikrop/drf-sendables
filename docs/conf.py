# type: ignore

import os
import sys
from pathlib import Path

import django
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.db.models.query_utils import DeferredAttribute

sys.path.insert(0, str(Path(__file__).parent.parent))
import sendables  # noqa: E402

os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
django.setup()
from django.contrib.contenttypes.fields import GenericForeignKey  # noqa: E402

project = "drf-sendables"
copyright = "2024, Aristotelis Mikropoulos"
author = "Aristotelis Mikropoulos"
release = sendables.__version__
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinxcontrib.httpdomain",
    "sphinx_toolbox.confval",
]
autodoc_member_order = "bysource"
autosectionlabel_prefix_document = True
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["style.css"]


def customize_docstrings(app, what, name, obj, options, lines):
    if hasattr(obj, "_declared_fields") and obj._declared_fields:
        # Serializer class
        for field_name, field in obj._declared_fields.items():
            lines.append(f"**{field_name}:** {field}")
            lines.append("")

    elif isinstance(obj, (ForwardManyToOneDescriptor, DeferredAttribute)):
        # Model field
        lines[:] = [obj.field.__class__.__name__]

    elif isinstance(obj, GenericForeignKey):
        # Model generic foreign key
        lines[:] = ["GenericForeignKey"]


def setup(app):
    app.connect("autodoc-process-docstring", customize_docstrings)
