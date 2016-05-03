# Packages
from flask import Blueprint, Response
# PRoject
from datapunt_geosearch.datasource import AtlasDataSource, NapMeetboutenDataSource

health = Blueprint('health', __name__)


@health.route('/status/health', methods=['GET', 'HEAD', 'OPTIONS'])
def search_list():
    """Execute test query against datasources"""
    x, y, response_text = 120993, 485919, []
    try:
        atlas_dsn, nap_dsn = AtlasDataSource(), NapMeetboutenDataSource()
    except Exception as e:
        return repr(e), 500
    results = atlas_dsn.query(x, y)

    if not len(results['result']['features']):
        response_text.append('No results from atlas dataset')

    results = nap_dsn.query(x, y)

    if not len(results['result']['features']):
        response_text.append('No results from nap/meetbouten dataset')

    if not len(response_text):
        return Response(' - '.join(response_text), content_type='text/plain', status=500)

    return Response('Connectivity OK', content_type='text/plain')
