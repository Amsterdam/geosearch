import logging
import os
from pathlib import Path
from typing import Dict

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from datapunt_geosearch.authz import get_keyset

DATABASE_SET_ROLE = os.getenv("DATABASE_SET_ROLE", False)
CLOUD_ENV = os.getenv("CLOUD_ENV", "CLOUDVPS")

db_connection_string = "postgresql://{username}:{password}@{host}:{port}/{db}"

# Configure OpenTelemetry to use Azure Monitor with the
# APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
TELEMETRY_TO_CONSOLE = os.getenv("TELEMETRY_TO_CONSOLE", False)
if APPLICATIONINSIGHTS_CONNECTION_STRING is not None:
    configure_azure_monitor(
        logger_name="root",
        instrumentation_options={
            "azure_sdk": {"enabled": False},
            "django": {"enabled": False},
            "fastapi": {"enabled": False},
            "flask": {"enabled": False},  # Configure flask manually
            "psycopg2": {"enabled": False},  # Configure psycopg2 manually
            "requests": {"enabled": True},
            "urllib": {"enabled": False},
            "urllib3": {"enabled": True},
        },
        resource=Resource.create({SERVICE_NAME: "Geosearch"}),
    )
    logger = logging.getLogger("root")
    logger.info("OpenTelemetry has been enabled")
elif TELEMETRY_TO_CONSOLE:
    # Setup opentelemetry for exporting to console
    resource = Resource(attributes={SERVICE_NAME: "Geosearch"})

    traceProvider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    traceProvider.add_span_processor(processor)
    trace.set_tracer_provider(traceProvider)

    reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
    meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meterProvider)


def get_db_settings(db_key: str) -> Dict[str, str]:
    """
    Get the complete settings for a given database. Taking all possible
    environments into account.

    :rtype: Dict[str, str]
    :param db_key: the key used as env var prefix
    :param docker_host:
    :param localport:
    :return: A dict containing all settings:
             'username', 'password', 'host', 'port' and 'db'
    """
    db = os.getenv(f"{db_key.upper()}_DB_DATABASE_OVERRIDE", db_key)
    password = os.getenv(f"{db_key.upper()}_DB_PASSWORD_OVERRIDE")
    if CLOUD_ENV.lower() == "azure":
        try:
            # Note that the secrets are named after the name of the db in Azure
            # in stead of the db_key used to get settings from the environment.
            location = os.environ[f"{db_key.upper()}_PW_LOCATION"]
            password = Path(location).read_text()
        except KeyError:
            # In this case we are testing on Azure
            pass

    return {
        "username": os.environ[f"{db_key.upper()}_DB_USER_OVERRIDE"],
        "password": password,
        "host": os.environ[f"{db_key.upper()}_DB_HOST_OVERRIDE"],
        "port": os.getenv(f"{db_key.upper()}_DB_PORT_OVERRIDE", "5432"),
        "db": db,
    }


DATAPUNT_API_URL = os.getenv("DATAPUNT_API_URL", "https://api.data.amsterdam.nl/")


JWKS_TEST_KEY = """
    {
        "keys": [
            {
                "kty": "EC",
                "key_ops": [
                    "verify",
                    "sign"
                ],
                "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
                "crv": "P-256",
                "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
                "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
                "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
            }
        ]
    }
"""

JWKS = os.getenv("PUB_JWKS", JWKS_TEST_KEY)
JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL")
JWKS_SIGNING_ALGORITHMS = [
    "ES256",
    "ES384",
    "ES512",
    "RS256",
    "RS384",
    "RS512",
]

JW_KEYSET = get_keyset(jwks=JWKS, jwks_url=JWKS_URL)
