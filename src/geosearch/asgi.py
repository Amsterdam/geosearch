# ASGI entrypoint for running Django under an ASGI server (e.g. uvicorn)
# See: https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geosearch.settings")

application = get_asgi_application()
