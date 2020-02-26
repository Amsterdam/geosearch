"""
Contains the different configs for the datapunt geosearch application
"""
import json
import logging
import os
from typing import Dict

import yaml

import sentry_sdk

logger = logging.getLogger(__name__)


def in_docker() -> bool:
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
    :rtype: bool
    :return: true when running in a docker container, false otherwise
    """
    # noinspection PyBroadException
    try:
        cgroup = open('/proc/1/cgroup', 'r').read()
        return ':/docker/' in cgroup or ':/docker-ce/' in cgroup
    except:
        return False


def get_variable(db: str, varname: str, docker_default: str,
                 sa_default: str = None) -> str:
    """
    Retrieve variables taking into account env overrides and wetter we are
    running in Docker or standalone (development)

    :rtype: str
    :param db: The database for which we are retrieving settings
    :param varname: The variable to retrieve
    :param docker_default: The default value (Running in docker)
    :param sa_default: The default value (Running standalone)
    :return: The applicable value of the requested variable
    """
    sa_default = docker_default if sa_default is None else sa_default

    return os.getenv(f"{db}_DB_{varname}_OVERRIDE".upper(),
                     docker_default if in_docker() else sa_default)


def get_db_settings(db: str, docker_host: str, localport: str) -> Dict[str, str]:
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
        'username': get_variable(db=db, varname='user', docker_default=db),
        'password': get_variable(db=db, varname='password',
                                 docker_default='insecure'),
        'host': get_variable(db=db, varname='host', docker_default=docker_host,
                             sa_default='localhost'),
        'port': get_variable(db=db, varname='port', docker_default='5432',
                             sa_default=localport),
        'db': get_variable(db=db, varname='database', docker_default=db)
    }


_db_connection_string = 'postgresql://{username}:{password}@{host}:{port}/{db}'


DSN_BAG = _db_connection_string.format(
    **get_db_settings(db='bag_v11',
                      docker_host='bag_v11_db',
                      localport='5405'))

DSN_NAP = _db_connection_string.format(
    **get_db_settings(db='nap',
                      docker_host='nap_db',
                      localport='5401'))

DSN_MILIEU = _db_connection_string.format(
    **get_db_settings(db='milieuthemas',
                      docker_host='milieuthemas_db',
                      localport='5402'))

# DSN_TELLUS = _db_connection_string.format(
#     **get_db_settings(db='tellus',
#                       docker_host='tellus_db',
#                       localport='5409'))

DSN_MONUMENTEN = _db_connection_string.format(
    **get_db_settings(db='monumenten',
                      docker_host='monumenten_db',
                      localport='5412'))


DSN_VARIOUS_SMALL_DATASETS = _db_connection_string.format(
    **get_db_settings(db='various_small_datasets',
                      docker_host='various_small_datasets_db',
                      localport='5408'))


DSN_DATASERVICES_DATASETS = _db_connection_string.format(
    **get_db_settings(db='dataservices',
                      docker_host='dataservices_db',
                      localport='5409'))


logging.debug('Database config:\n'
              'Bag: %s\n'
              'Nap: %s\n'
              'Milieu: %s\n'
 #             'Tellus: %s\n'
              'Monumenten: %s\n',
              'Various Small Datasets',
              DSN_BAG, DSN_NAP, DSN_MILIEU, DSN_MONUMENTEN, DSN_VARIOUS_SMALL_DATASETS)

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


def load_jwks_config(filename):

    with open(filename, 'r') as config_file:
        try:
            config = yaml.load(config_file)
            if 'jwks' in config:
                config['jwks'] = json.loads(config['jwks'])
        except (yaml.YAMLError,
                json.decoder.JSONDecodeError) as error_details:
            logger.error(
                "Failed to load config: %s Error: %s",
                filename,
                repr(error_details)
            )
            return None, None, None

    return config['jwks'], config.get('jwks_url'), config.get('jwks_allowed_signing_algorithms')


default_config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
JWKS, JWKS_URL, JWKS_SIGNING_ALGORITHMS = load_jwks_config(default_config_file)

global_config_file = os.getenv("GEOSEARCH_CONFIG_PATH", "/etc/geosearch.yaml")
if os.path.exists(global_config_file):
    JWKS, JWKS_URL, JWKS_SIGNING_ALGORITHMS = load_jwks_config(
        default_config_file)
