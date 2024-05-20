import logging
import os

from datapunt_geosearch.base_config import DATAPUNT_API_URL  # noqa
from datapunt_geosearch.base_config import JW_KEYSET  # noqa
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from datapunt_geosearch.base_config import (  # noqa, this is imported from config.py and essential; noqa: F401
    DATABASE_SET_ROLE,
    JWKS,
    db_connection_string,
    get_db_settings,
)

dataservices_settings = get_db_settings("dataservices")
DSN_DATASERVICES_DATASETS = db_connection_string.format(**dataservices_settings)
DATASERVICES_USER = dataservices_settings["username"]


# Configure OpenTelemetry to use Azure Monitor with the
# APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APPLICATIONINSIGHTS_CONNECTION_STRING is not None:
    configure_azure_monitor(logger_name="root", instrumentation_options = {
        "azure_sdk": {"enabled": False},
        "django": {"enabled": False},
        "fastapi": {"enabled": False},
        "flask": {"enabled": False}, # Configure flask manually
        "psycopg2": {"enabled": False}, # Configure psycopg2 manually
        "requests": {"enabled": True},
        "urllib": {"enabled": False},
        "urllib3": {"enabled": True},
    }, resource=Resource.create({SERVICE_NAME: "Geosearch"}))
    logger = logging.getLogger("root")
    logger.info("OpenTelemetry has been enabled")

logging.debug(
    "\n\nApp Database config:\n\
        Dataservices: %s\n\
        Role switching %s\n\n",
    DSN_DATASERVICES_DATASETS,
    "active" if DATABASE_SET_ROLE else "inactive",
)
