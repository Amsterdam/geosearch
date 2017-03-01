"""
Contains the different configs for the datapunt geosearch application
"""
import os


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


def get_var(db, varname, default):
    return os.getenv(f"{db}_DB_{varname}_OVERRIDE".upper(), default)


DB_SETTINGS = {
    'ATLAS': {
        'host': get_var('atlas', 'host', 'atlas_db'),
        'port': get_var('atlas', 'port', 5432),
        'database': get_var('atlas', 'database', 'atlas'),
        'user': get_var('atlas', 'user', 'atlas'),
        'password': get_var('atlas', 'password', 'insecure')
    },
    'NAP': {
        'host': get_var('nap', 'host', 'nap_db'),
        'port': get_var('nap', 'port', 5432),
        'database': get_var('nap', 'database', 'nap'),
        'user': get_var('nap', 'user', 'nap'),
        'password': get_var('nap', 'password', 'insecure')
    },
    'MILIEU': {
        'host': get_var('milieu', 'host', 'milieu_db'),
        'port': get_var('milieu', 'port', 5432),
        'database': get_var('milieu', 'database', 'milieuthemas'),
        'user': get_var('milieu', 'user', 'milieuthemas'),
        'password': get_var('milieu', 'password', 'insecure')
    },
    'TELLUS': {
        'host': get_var('tellus', 'host', 'tellus_db'),
        'port': get_var('tellus', 'port', 5432),
        'database': get_var('tellus', 'database', 'tellus'),
        'user': get_var('tellus', 'user', 'tellus'),
        'password': get_var('tellus', 'password', 'insecure')
    }
} if in_docker() else {
    'ATLAS': {
        'host': get_var('atlas', 'host', 'localhost'),
        'port': get_var('atlas', 'port', 5405),
        'database': get_var('atlas', 'database', 'atlas'),
        'user': get_var('atlas', 'user', 'atlas'),
        'password': get_var('atlas', 'password', 'insecure')
    },
    'NAP': {
        'host': get_var('nap', 'host', 'localhost'),
        'port': get_var('nap', 'port', 5401),
        'database': get_var('nap', 'database', 'nap'),
        'user': get_var('nap', 'user', 'nap'),
        'password': get_var('nap', 'password', 'insecure')
    },
    'MILIEU': {
        'host': get_var('milieu', 'host', 'localhost'),
        'port': get_var('milieu', 'port', 5402),
        'database': get_var('milieu', 'database', 'milieuthemas'),
        'user': get_var('milieu', 'user', 'milieuthemas'),
        'password': get_var('milieu', 'password', 'insecure')
    },
    'TELLUS': {
        'host': get_var('tellus', 'host', 'localhost'),
        'port': get_var('tellus', 'port', 5409),
        'database': get_var('tellus', 'database', 'tellus'),
        'user': get_var('tellus', 'user', 'tellus'),
        'password': get_var('tellus', 'password', 'insecure')
    }
}

print(DB_SETTINGS)

DSN_ATLAS = 'postgresql://{}:{}@{}:{}/{}'.format(
    DB_SETTINGS['ATLAS']['user'],
    DB_SETTINGS['ATLAS']['password'],
    DB_SETTINGS['ATLAS']['host'],
    DB_SETTINGS['ATLAS']['port'],
    DB_SETTINGS['ATLAS']['database']
)

DSN_NAP = 'postgresql://{}:{}@{}:{}/{}'.format(
    DB_SETTINGS['NAP']['user'],
    DB_SETTINGS['NAP']['password'],
    DB_SETTINGS['NAP']['host'],
    DB_SETTINGS['NAP']['port'],
    DB_SETTINGS['NAP']['database']
)

DSN_MILIEU = 'postgresql://{}:{}@{}:{}/{}'.format(
    DB_SETTINGS['MILIEU']['user'],
    DB_SETTINGS['MILIEU']['password'],
    DB_SETTINGS['MILIEU']['host'],
    DB_SETTINGS['MILIEU']['port'],
    DB_SETTINGS['MILIEU']['database']
)

DSN_TELLUS = 'postgresql://{}:{}@{}:{}/{}'.format(
    DB_SETTINGS['TELLUS']['user'],
    DB_SETTINGS['TELLUS']['password'],
    DB_SETTINGS['TELLUS']['host'],
    DB_SETTINGS['TELLUS']['port'],
    DB_SETTINGS['TELLUS']['database']
)
