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


