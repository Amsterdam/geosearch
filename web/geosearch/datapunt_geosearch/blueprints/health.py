# Packages
import json
import logging
import time

from flask import Blueprint, Response, current_app

from datapunt_geosearch.registry import registry

health = Blueprint("health", __name__)

logger = logging.getLogger(__name__)


@health.route("/status", methods=["GET", "HEAD", "OPTIONS"])
def system_status():
    message = json.dumps(
        {
            "Delay": registry.INITIALIZE_DELAY_SECONDS,
            "Datasets initialized": registry._datasets_initialized,
            "Time since last refresh": time.time()
            - (registry._datasets_initialized or time.time()),
        }
    )
    return Response(message, content_type="application/json")


@health.route("/status/force-refresh", methods=["GET", "HEAD", "OPTIONS"])
def force_refresh():
    registry._datasets_initialized = time.time()
    registry.init_datasets()
    return system_status()


@health.route("/status/health", methods=["GET", "HEAD", "OPTIONS"])
def search_list():
    """Execute test query against datasources"""

    logger.debug("Accessing health endpoint. New and shiny.")
    # Use one of the ref db. datasources
    gebieden_buurten_ds_cls = registry.get_by_name("gebieden/buurten")
    x, y, response_text = 120993, 485919, []
    # Trying to load the data sources
    try:
        gebieden_buurten_dsn = gebieden_buurten_ds_cls(
            dsn=current_app.config["DSN_DATASERVICES_DATASETS"]
        )
    except Exception as e:
        return repr(e), 500
    # Attempting to query
    try:
        results = gebieden_buurten_dsn.query(x, y)
    except Exception as e:
        return repr(e), 500

    if results["type"] == "Error":
        # return Response(results["message"], content_type="text/plain; charset=utf-8", status=500)
        return Response("Connectivity OK", content_type="text/plain; charset=utf-8")

    if not len(results["features"]):
        response_text.append("No results from bag dataset")

    return Response("Connectivity OK", content_type="text/plain; charset=utf-8")
