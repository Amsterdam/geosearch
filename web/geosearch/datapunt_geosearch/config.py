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


def get_db_settings(db: str, consul_host: str, localport: str) -> Dict[
    str, str]:
    """
    Get the complete settings for a given database. Taking all possible
    environments into account.

    :rtype: Dict[str, str]
    :param db:
    :param consul_host:
    :param localport:
    :return: A dict containing all settings:
             'username', 'password', 'host', 'port' and 'db'
    """
    return {
        'username': get_variable(db=db, varname='user', docker_default=db),
        'password': get_variable(db=db, varname='password',
                                 docker_default='insecure'),
        'host': get_variable(db=db, varname='host', docker_default=consul_host,
                             sa_default='localhost'),
        'port': get_variable(db=db, varname='port', docker_default='5432',
                             sa_default=localport),
        'db': get_variable(db=db, varname='database', docker_default=db)
    }


DSN_ATLAS = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='atlas',
                      consul_host='atlas_db',
                      localport='5405'))

DSN_NAP = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='nap',
                      consul_host='nap_db',
                      localport='5401'))

DSN_MILIEU = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='milieuthemas',
                      consul_host='milieuthemas_db',
                      localport='5402'))

DSN_TELLUS = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='tellus',
                      consul_host='tellus_db',
                      localport='5409'))

DSN_MONUMENTEN = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='monumenten',
                      consul_host='monumenten_db',
                      localport='5412'))

logging.debug('Database config:\n'
              'Atlas: %s\n'
              'Nap: %s\n'
              'Milieu: %s\n'
              'Tellus: %s\n'
              'Monumenten: %s',
              DSN_ATLAS, DSN_NAP, DSN_MILIEU, DSN_TELLUS, DSN_MONUMENTEN)
