import os
import sys

import django
from django.conf import settings
from django.core.management import call_command
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()

    # Use different migrations directory for each tox environment,
    # for tox parallel run to work correctly.
    tox_env_name = os.getenv("TOX_ENV_NAME", "test")
    settings.MIGRATION_MODULES = {
        "sendables": "sendables.migrations." + tox_env_name,
        "tests": "tests.migrations." + tox_env_name,
    }

    call_command("makemigrations", "sendables")
    call_command("makemigrations", "tests")

    # Use shortcuts for test labels.
    labels = ["tests.test_" + label for label in sys.argv[1:]]

    TestRunner = get_runner(settings)
    failures = TestRunner().run_tests(labels)

    sys.exit(bool(failures))
