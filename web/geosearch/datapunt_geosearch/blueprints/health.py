# Packages
from flask import Blueprint, Response, current_app

from datapunt_geosearch.datasource import AtlasDataSource, \
    NapMeetboutenDataSource

health = Blueprint('health', __name__)


@health.route('/status/health', methods=['GET', 'HEAD', 'OPTIONS'])
def search_list():
    """Execute test query against datasources"""
    x, y, response_text = 120993, 485919, []
    # Trying to load the data sources
    try:
        atlas_dsn = AtlasDataSource(dsn=current_app.config['DSN_ATLAS'])
        nap_dsn = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
    except Exception as e:
        return repr(e), 500
    # Attempting to query
    try:
        results = atlas_dsn.query(x, y)
    except Exception as e:
        return repr(e), 500

    if results['type'] == 'Error':
        return Response(results['message'],
                        content_type='text/plain; charset=utf-8',
                        status=500)

    if not len(results['features']):
        response_text.append('No results from atlas dataset')

    results = nap_dsn.query(x, y)

    if not len(results['features']):
        response_text.append('No results from nap/meetbouten dataset')

    if not len(response_text):
        return Response(' - '.join(response_text),
                        content_type='text/plain; charset=utf-8',
                        status=500)

    return Response('Connectivity OK',
                    content_type='text/plain; charset=utf-8')
