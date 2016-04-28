# Python
import json
# Packages
from flask import Blueprint, request
# PRoject
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
