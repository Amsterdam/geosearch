"""
Contains the different configs for the datapunt geosearch application
"""
import os
from typing import Dict


def in_docker():
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
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
    :param db: The database for which we are retrieving settings
    :param varname: The variable to retrieve
    :param docker_default: The default value (Running in docker)
    :param sa_default: The default value (Running standalone)
    :return: The applicable value of the requested variable
    """
    sa_default = docker_default if sa_default is None else sa_default

    return os.getenv(f"{db}_DB_{varname}_OVERRIDE".upper(),
                     docker_default if in_docker() else sa_default)


def get_db_settings(db: str, consul_host: str, localport: str) -> Dict[str, str]:
    """
    Get the complete settings for a given database. Taking all possible
    environments into account.
    :param db:
    :param consul_host:
    :param localport:
    :return: A dict containing all settings:
             'username', 'password', 'host', 'port' and 'db'
    """
    return {
        'username': get_variable(db, 'user', db),
        'password': get_variable(db, 'password', 'insecure'),
        'host': get_variable(db, 'host', consul_host, 'localhost'),
        'port': get_variable(db, 'port', '5432', localport),
        'db': get_variable(db, 'database', db)
    }


DSN_ATLAS = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='atlas', consul_host='atlas_db', localport='5405')
)

DSN_NAP = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='nap', consul_host='nap_db', localport='5401')
)

DSN_MILIEU = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='milieu', consul_host='milieu_db', localport='5402')
)

DSN_TELLUS = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='tellus', consul_host='tellus_db', localport='5409')
)

DSN_MONUMENTEN = 'postgresql://{username}:{password}@{host}:{port}/{db}'.format(
    **get_db_settings(db='monumenten', consul_host='monumenten_db', localport='5412')
)

print(DSN_ATLAS, DSN_MILIEU, DSN_NAP, DSN_TELLUS, DSN_MONUMENTEN, sep='\n')
