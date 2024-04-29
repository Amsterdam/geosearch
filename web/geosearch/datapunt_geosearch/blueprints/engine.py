import logging

from schematools.naming import to_snake_case

try:
    import orjson as json
except ImportError:
    import json

from flask import current_app as app

from datapunt_geosearch.registry import registry

_logger = logging.getLogger(__name__)


def generate_async(request_args, authz_scopes=None):
    datasets = request_args.get("datasets").split(",")
    first_item = True
    yield '{"type": "FeatureCollection", "features": ['
    for ds in registry.filter_datasources(names=datasets, scopes=authz_scopes):
        for row in fetch_data(ds, request_args, datasets):
            if first_item:
                first_item = False
            else:
                yield ","
            yield json.dumps(row)
    yield "]}"


def fetch_data(sourceClass, request_args, datasets):
    dsn = None
    if sourceClass.dsn_name is not None:
        try:
            dsn = app.config[sourceClass.dsn_name]
        except AttributeError:
            _logger.error(
                "Can not find configuration for %s." % sourceClass.dsn_name,
                exc_info=True,
            )
            return []

    datasource = sourceClass(dsn=dsn)
    datasource.use_rd = request_args["rd"]
    datasource.x = float(request_args["x"])
    datasource.y = float(request_args["y"])
    if request_args.get("radius"):
        datasource.radius = request_args.get("radius")

    if request_args["limit"]:
        datasource.limit = request_args["limit"]

    if field_names_in_query := request_args.get("_fields", "").split(","):
        # We collect extra field_names that need to be in the resulting response
        datasource.field_names_in_query = [to_snake_case(fn) for fn in field_names_in_query if fn]

    try:
        response = datasource.execute_queries(datasets=datasets)
    except Exception:
        _logger.error("Failed to fetch data from %s" % datasource, exc_info=True)
        return []
    else:
        return response
