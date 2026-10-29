"""WSGI config for the geosearch project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geosearch.settings")

application = get_wsgi_application()
