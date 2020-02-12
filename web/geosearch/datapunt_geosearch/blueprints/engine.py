import concurrent.futures
from functools import partial
import logging
try:
    import orjson as json
except ImportError:
    import json

from datapunt_geosearch.config import DEFAULT_SEARCH_DATASETS
from datapunt_geosearch.registry import registry


_logger = logging.getLogger(__name__)


def generate_async(request_args):
    if request_args.get('datasets'):
        datasets = request_args.get('datasets').split(',')
    else:
        datasets = DEFAULT_SEARCH_DATASETS

    fetch = partial(fetch_data, request_args=request_args, datasets=datasets)
    first_item = True
    yield '{"type": "FeatureCollection", "features": ['
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for result in executor.map(fetch, registry.filter_datasets(names=datasets), timeout=1):
            for row in result:
                if first_item:
                    first_item = False
                else:
                    yield ','
                yield json.dumps(row)
    yield ']}'


def fetch_data(sourceClass, request_args, datasets, retry=None):
    from datapunt_geosearch import config
    try:
        dsn = getattr(config, sourceClass.dsn_name)
    except AttributeError:
        _logger.error("Can not find configuration for {}.".format(
            sourceClass.dsn_name
        ), exc_info=True)
        return []

    datasource = sourceClass(dsn=dsn)
    datasource.use_rd = request_args['rd']
    datasource.x = float(request_args['x'])
    datasource.y = float(request_args['y'])

    if request_args.get('radius'):
        datasource.radius = request_args.get('radius')

    if request_args['limit']:
        datasource.limit = request_args['limit']

    try:
        response = datasource.execute_queries(datasets=datasets)
    except Exception:
        _logger.error("Failed to fetch data from {}".format(datasource), exc_info=True)
        return []
    else:
        return response
