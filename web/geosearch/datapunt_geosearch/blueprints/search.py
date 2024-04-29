# Python
import logging

from flask import Blueprint, Response, jsonify, request, send_from_directory, stream_with_context

from datapunt_geosearch.authz import authenticate, get_current_authz_scopes
from datapunt_geosearch.blueprints.engine import generate_async
from datapunt_geosearch.registry import registry

search = Blueprint("search", __name__)

_logger = logging.getLogger(__name__)


def get_coords_and_type(args):
    """
    Retrieves the coordinates from the request and identifies if the request is
    in RD or in wgs84. If no coordinates are found an error message is set in a
    response dict. The RD flag is set to true if the coords given are in rd.

    @params
    args - The request args

    @Returns
    A tuple with the x, y, rd flag and response dict
    """
    resp = None
    rd = True

    x = args.get("x")
    y = args.get("y")
    limit = args.get("limit")

    if not x or not y:
        x = args.get("lat")
        y = args.get("lon")

        if x and y:
            rd = False
        else:
            resp = {"error": "No coordinates found"}

    return x, y, rd, limit, resp


@search.route("/docs/geosearch.yml", methods=["GET", "OPTIONS"])
def send_doc():
    return send_from_directory("static", "geosearch.yml", mimetype="application/x-yaml")


@search.route("/", methods=["GET", "OPTIONS"])
@authenticate
def search_everywhere():
    """
    Search in all datasets combined.
    Required arguments:
     - x/y or lat/lon for position
     - datasets - subset of datasets to search in.

    The `datasets` param is constructed as <dataset>/<table>
    For example:
        precariobelasting/bedrijfsvaartuigen
    """
    x, y, rd, limit, resp = get_coords_and_type(request.args)
    if resp:
        return jsonify(resp)

    request_args = dict(request.args)

    request_args.update(
        dict(
            x=x,
            y=y,
            rd=rd,
            limit=limit,
        )
    )

    return Response(
        stream_with_context(
            generate_async(request_args=request_args, authz_scopes=get_current_authz_scopes())
        ),
        content_type="application/json",
    )


@search.route("/catalogus/", methods=["GET"])
@authenticate
def search_catalogus():
    """Generate a list of all values that can be used as input to the root endpoint."""

    # Note that we filter the top-level keys as they are  defined in
    # DataSourceClass.metadata["datasets"] since it is completely illogical
    # and unpredictable for users of the API what the results will be when these
    # keys are used. They are not based on any known naming-scheme except for the
    # fact that they are used in this codebase.
    dataset_names = [
        name
        for name, dataset in registry.get_all_datasources().items()
        if dataset.check_scopes(scopes=get_current_authz_scopes()) and "/" in name
    ]

    return jsonify({"datasets": dataset_names})


# Adding cors headers
@search.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response
