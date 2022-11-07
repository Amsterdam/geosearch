import os
from logging.config import dictConfig
from typing import Dict

from datapunt_geosearch.authz import get_keyset

DATABASE_SET_ROLE = os.getenv("DATABASE_SET_ROLE", False)


def get_db_settings(db: str) -> Dict[str, str]:
    """
    Get the complete settings for a given database. Taking all possible
    environments into account.

    :rtype: Dict[str, str]
    :param db:
    :param docker_host:
    :param localport:
    :return: A dict containing all settings:
             'username', 'password', 'host', 'port' and 'db'
    """
    return {
        "username": os.environ[f"{db.upper()}_DB_USER_OVERRIDE"],
        "password": os.environ[f"{db.upper()}_DB_PASSWORD_OVERRIDE"],
        "host": os.environ[f"{db.upper()}_DB_HOST_OVERRIDE"],
        "port": os.getenv(f"{db.upper()}_DB_PORT_OVERRIDE", "5432"),
        "db": os.getenv(f"{db.upper()}_DB_DATABASE_OVERRIDE", db),
    }


db_connection_string = "postgresql://{username}:{password}@{host}:{port}/{db}"

DATAPUNT_API_URL = os.getenv("DATAPUNT_API_URL", "https://api.data.amsterdam.nl/")

DEFAULT_SEARCH_DATASETS = [
    "monumenten",
    "openbareruimte",
    "pand",
    "stadsdeel",
    "peilmerk",
    "meetbout",
    "uitgevoerdonderzoek",
    "bominslag",
]

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

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": os.getenv("LOG_LEVEL", "INFO"), "handlers": ["wsgi"]},
    }
)
