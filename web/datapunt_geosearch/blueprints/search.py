# Python
import json
# Packages
from flask import Blueprint, request, jsonify
# PRoject
from datapunt_geosearch.datasets import AtlasDataSource, NapMeetboutenDataSource
from datapunt_geosearch.elastic import Elastic

search = Blueprint('search', __name__)
es = Elastic()


@search.route('/search', methods=['GET'])
def search_list():
    """List search endpoints"""
    # @TODO can it be automated?
    return jsonify({'/search/geosearch': 'Search on the basis of geo information'})


@search.route('/search/geosearch', methods=['GET', 'POST'])
def search_geo():
    """Performing a geo search for radius around a point"""
    resp = None
    # Making sure point and radius are given
    radius = request.args.get("radius")
    if not radius:
        resp = {"error" : "Radius not found in get parameters"}
    # Checking either coords arra yor lat en lon
    coords = request.args.get('coords')
    if not coords:
        lon = request.args.get('lon')
        lat = request.args.get('lat')
        if not lat or not lon:
            resp = {"error" : "No coordinates found"}
        coords = [lon, lat]
    # @TODO add support for filter and exclude
    # If no error is found, query
    if not resp:
        resp = es.search_radius(coords, radius)
    return json.dumps(resp)


@search.route('/search/geosearch/nap', methods=['GET'])
def search_geo_nap():
    """Performing a geo search for radius around a point using postgres"""
    resp = None

    x = request.args.get('x')
    y = request.args.get('y')
    if not x or not y:
        resp = {'error': 'No coordinates found'}

    # If no error is found, query
    if not resp:
        ds = NapMeetboutenDataSource()
        resp = ds.query(x, y, radius=request.args.get('radius'))

    jsonify(resp)


@search.route('/search/geosearch/atlas', methods=['GET'])
def search_geo_atlas():
    """Performing a geo search for radius around a point using postgres"""
    resp = None

    x = request.args.get('x')
    y = request.args.get('y')
    if not x or not y:
        resp = {'error': 'No coordinates found'}

    # If no error is found, query
    if not resp:
        ds = AtlasDataSource()
        resp = ds.query(x, y)

    jsonify(resp)
