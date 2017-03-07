"""
Contains the different configs for the datapunt geosearch application
"""
import logging
import os
from typing import Dict

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
        return ':/docker/' in open('/proc/1/cgroup', 'r').read()
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

DSN_ATLAS = _db_connection_string.format(
    **get_db_settings(db='atlas',
                      docker_host='atlas_db',
                      localport='5405'))

DSN_NAP = _db_connection_string.format(
    **get_db_settings(db='nap',
                      docker_host='nap_db',
                      localport='5401'))

DSN_MILIEU = _db_connection_string.format(
    **get_db_settings(db='milieuthemas',
                      docker_host='milieuthemas_db',
                      localport='5402'))

DSN_TELLUS = _db_connection_string.format(
    **get_db_settings(db='tellus',
                      docker_host='tellus_db',
                      localport='5409'))

DSN_MONUMENTEN = _db_connection_string.format(
    **get_db_settings(db='monumenten',
                      docker_host='monumenten_db',
                      localport='5412'))

logging.debug('Database config:\n'
              'Atlas: %s\n'
              'Nap: %s\n'
              'Milieu: %s\n'
              'Tellus: %s\n'
              'Monumenten: %s',
              DSN_ATLAS, DSN_NAP, DSN_MILIEU, DSN_TELLUS, DSN_MONUMENTEN)
