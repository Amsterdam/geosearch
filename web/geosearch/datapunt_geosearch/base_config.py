import logging
import os
from pathlib import Path
from typing import Dict

from datapunt_geosearch.authz import get_keyset

DATABASE_SET_ROLE = os.getenv("DATABASE_SET_ROLE", False)
CLOUD_ENV = os.getenv("CLOUD_ENV", "CLOUDVPS")

db_connection_string = "postgresql://{username}:{password}@{host}:{port}/{db}"

DSN_ADMIN_USER = ""  # needs an initial value, because is imported from elsewhere
# On Azure we need a superuser to configure end user context in tests
if CLOUD_ENV.lower() == "azure":
    DSN_ADMIN_USER = db_connection_string.format(
        **{
            "username": os.environ.get("TEST_ADMIN_USER", "testuser"),
            "password": os.environ.get("TEST_ADMIN_PASSWORD", "insecure"),
            "host": os.environ.get("TEST_ADMIN_HOST", "testdb-svc"),
            "port": os.environ.get("TEST_ADMIN_PORT", 5432),
            "db": os.environ.get("TEST_ADMIN_DB", "dataservices"),
        }
    )


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
