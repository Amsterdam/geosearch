"""
Contains the different configs for the datapunt geosearch application
"""
import os
import re


def get_docker_host():
    """
    Looks for the DOCKER_HOST environment variable to find the VM
    running docker-machine.

    If the environment variable is not found, it is assumed that
    you're running docker on localhost.
    """
    d_host = os.getenv('DOCKER_HOST', None)
    if d_host:
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', d_host):
            return d_host

        return re.match(r'tcp://(.*?):\d+', d_host).group(1)
    return os.getenv('NAP_DB_PORT_5432_TCP_ADDR', 'localhost')


DSN_ATLAS = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('ATLAS_DB_USER', 'atlas'),
    os.getenv('ATLAS_DB_PASSWORD', 'insecure'),
    os.getenv('ATLAS_DB_PORT_5432_TCP_ADDR', get_docker_host()),
    os.getenv('ATLAS_DB_PORT_5432_TCP_PORT', 5405),
    os.getenv('ATLAS_DB_NAME', 'atlas'),
)

DSN_NAP = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('NAP_DB_USER', 'nap'),
    os.getenv('NAP_DB_PASSWORD', 'insecure'),
    os.getenv('NAP_DB_PORT_5432_TCP_ADDR', get_docker_host()),
    os.getenv('NAP_DB_PORT_5432_TCP_PORT', 5401),
    os.getenv('NAP_DB_NAME', 'nap'),
)

DSN_MILIEU = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('MILIEU_DB_USER', 'milieuthemas'),
    os.getenv('MILIEU_DB_PASSWORD', 'insecure'),
    os.getenv('MILIEU_DB_PORT_5432_TCP_ADDR', get_docker_host()),
    os.getenv('MILIEU_DB_PORT_5432_TCP_PORT', 5402),
    os.getenv('MILIEU_DB_NAME', 'milieuthemas'),
)

DSN_TELLUS = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('TELLUS_DB_USER', 'tellus'),
    os.getenv('TELLUS_DB_PASSWORD', 'insecure'),
    os.getenv('TELLUS_DB_PORT_5432_TCP_ADDR', get_docker_host()),
    os.getenv('TELLUS_DB_PORT_5432_TCP_PORT', 5409),
    os.getenv('TELLUS_DB_NAME', 'tellus'),
)

DSN_MONUMENTEN = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.getenv('MONUMENTEN_DB_USER', 'monumenten'),
    os.getenv('MONUMENTEN_DB_PASSWORD', 'insecure'),
    os.getenv('MONUMENTEN_DB_PORT_5432_TCP_ADDR', get_docker_host()),
    os.getenv('MONUMENTEN_DB_PORT_5432_TCP_PORT', 5412),
    os.getenv('MONUMENTEN_DB_NAME', 'monumenten'),
)
