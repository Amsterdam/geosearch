# Python
import json
# Packages
from flask import Blueprint, request, jsonify, current_app
# Project
from datapunt_geosearch.datasource import AtlasDataSource
from datapunt_geosearch.datasource import NapMeetboutenDataSource

search = Blueprint('search', __name__)



@search.route('/', methods=['GET'])
def help():
    """Help text en query index"""
    return json.dumps({
        '/nap': 'Search in a radius around a point in nap',
        '/atlas': 'Search in a radius around a point in atlas'
    })


@search.route('/nap/', methods=['GET', 'OPTIONS'])
def search_geo_nap():
    """Performing a geo search for radius around a point using postgres"""
    resp, rd = None, True

    x = request.args.get('x')
    y = request.args.get('y')

    if not x or not y:
        x = request.args.get('lat')
        y = request.args.get('lon')

        if x and y:
            rd = False
        else:
            resp = {'error': 'No coordinates found'}

    # If no error is found, query
    if not resp:
        ds = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
        resp = ds.query(float(x), float(y), rd=rd, radius=request.args.get('radius'))

    return jsonify(resp)


@search.route('/atlas/', methods=['GET', 'OPTIONS'])
def search_geo_atlas():
    """Performing a geo search for radius around a point using postgres"""
    resp, rd = None, True

    x = request.args.get('x')
    y = request.args.get('y')

    if not x or not y:
        x = request.args.get('lat')
        y = request.args.get('lon')

        if x and y:
            rd = False
        else:
            resp = {'error': 'No coordinates found'}

    # If no error is found, query
    if not resp:
        ds = AtlasDataSource(dsn=current_app.config['DSN_ATLAS'])
        resp = ds.query(float(x), float(y), rd=rd)

    return jsonify(resp)


# Adding cors headers
@search.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add(
        'Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response
