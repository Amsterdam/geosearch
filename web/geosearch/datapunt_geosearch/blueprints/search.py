# Python
import json
# Packages
from flask import Blueprint, request, jsonify, current_app
# Project
from datapunt_geosearch.datasource import AtlasDataSource, BommenMilieuDataSource
from datapunt_geosearch.datasource import NapMeetboutenDataSource

search = Blueprint('search', __name__)


def get_coords_and_type(args):
    """
    Retrieves the coordinates from the request
    and identifies if the request is in RD or in
    wgs84
    If no coordinates are found an error message is set in a
    response dict.
    The RD flag is set to true if the coords
    given are in rd.

    @params
    args - The request args

    @Returns
    A tuple with the x, y, rd flag and response dict
    """
    resp, rd = None, True

    x = args.get('x')
    y = args.get('y')

    if not x or not y:
        x = args.get('lat')
        y = args.get('lon')

        if x and y:
            rd = False
        else:
            resp = {'error': 'No coordinates found'}

    return (x, y, rd, resp)


@search.route('/search/', methods=['GET', 'OPTIONS'])
def search_in_radius():
    """
    General geosearch endpoint.
    Required arguments:
    x/y or lat/lon for position
    radius - search radius in meters
    item - Search item. adressen, meetbouten, kadastrale_objecten etc
    """
    x, y, rd, resp = get_coords_and_type(request.args)
    # If no coords are given, return
    if resp:
        return jsonify(resp)

    # Checking for radius and item type
    radius = request.args.get('radius')
    if not radius:
        return jsonify({'error': 'No radius found'})
    item = request.args.get('item')
    if not item:
        return jsonify({'error': 'No item type found'})

    # Got coords, radius and item. Time to search
    if item in ['peilmerk', 'meetbout']:
        ds = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
    elif item in ['bominslag', 'gevrijwaardgebied', 'uitgevoerdonderzoek', 'verdachtgebied']:
        ds = BommenMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
    else:
        ds = AtlasDataSource(dsn=current_app.config['DSN_ATLAS'])
    # Filtering to the required dataset
    known_dataset = ds.filter_dataset(item)
    if not known_dataset:
        return jsonify({'error': 'Unknown item type'})

    resp = ds.query(float(x), float(y), rd=rd, radius=radius)
    return jsonify(resp)


@search.route('/help/', methods=['GET', 'OPTIONS'])
def help():
    print(current_app.config)
    """Help text en query index"""
    return json.dumps({
        '/nap': 'Search in a radius around a point in nap',
        '/atlas': 'Search in a radius around a point in atlas'
    })


@search.route('/nap/', methods=['GET', 'OPTIONS'])
def search_geo_nap():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, resp = get_coords_and_type(request.args)
    print(resp)
    # If no error is found, query
    if not resp:
        ds = NapMeetboutenDataSource(dsn=current_app.config['DSN_NAP'])
        resp = ds.query(float(x), float(y), rd=rd, radius=request.args.get('radius'))

    return jsonify(resp)


@search.route('/bommen/', methods=['GET', 'OPTIONS'])
def search_geo_minutie():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, resp = get_coords_and_type(request.args)
    print(resp)
    # If no error is found, query
    if not resp:
        ds = BommenMilieuDataSource(dsn=current_app.config['DSN_MILIEU'])
        resp = ds.query(float(x), float(y), rd=rd, radius=request.args.get('radius'))

    return jsonify(resp)


@search.route('/atlas/', methods=['GET', 'OPTIONS'])
def search_geo_atlas():
    """Performing a geo search for radius around a point using postgres"""
    x, y, rd, resp = get_coords_and_type(request.args)

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
