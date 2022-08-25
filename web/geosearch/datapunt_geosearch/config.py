"""
Contains the different configs for the datapunt geosearch application
"""
import logging
import os
from typing import Dict

from datapunt_geosearch.authz import get_keyset

logger = logging.getLogger(__name__)


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
        'username': os.environ[f"{db.upper()}_DB_USER_OVERRIDE"],
        'password': os.environ[f"{db.upper()}_DB_PASSWORD_OVERRIDE"],
        'host': os.environ[f"{db.upper()}_DB_HOST_OVERRIDE"] ,
        'port': os.getenv(f"{db.upper()}_DB_PORT_OVERRIDE", "5432"),
        'db': db,
    }


_db_connection_string = 'postgresql://{username}:{password}@{host}:{port}/{db}'




def _make_conn_str(db: str) -> str:
    return _db_connection_string.format(**get_db_settings(db))


DSN_BAG = _make_conn_str('bag_v11')
DSN_NAP = _make_conn_str('nap')
DSN_MILIEU = _make_conn_str('milieuthemas')
DSN_MONUMENTEN = _make_conn_str('monumenten')
DSN_VARIOUS_SMALL_DATASETS = _make_conn_str('various_small_datasets')
DSN_DATASERVICES_DATASETS = _make_conn_str('dataservices')

logging.debug('Database config:\n'
              'Bag: %s\n'
              'Nap: %s\n'
              'Milieu: %s\n'
              'Monumenten: %s\n',
              'Various Small Datasets: %s\n',
              'Dataservices: %s\n',
              DSN_BAG, DSN_NAP, DSN_MILIEU, DSN_MONUMENTEN, DSN_VARIOUS_SMALL_DATASETS, DSN_DATASERVICES_DATASETS)

DATAPUNT_API_URL = os.getenv(
    'DATAPUNT_API_URL', 'https://api.data.amsterdam.nl/')

DEFAULT_SEARCH_DATASETS = [
    'monumenten',
    'openbareruimte',
    'pand',
    'stadsdeel',
    'peilmerk',
    'meetbout',
    'uitgevoerdonderzoek',
    'bominslag'
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

JWKS = os.getenv('PUB_JWKS', JWKS_TEST_KEY)
JWKS_URL = os.getenv('KEYCLOAK_JWKS_URL')
JWKS_SIGNING_ALGORITHMS = [
    'ES256',
    'ES384',
    'ES512',
    'RS256',
    'RS384',
    'RS512',
]

JW_KEYSET = get_keyset(jwks=JWKS, jwks_url=JWKS_URL)
