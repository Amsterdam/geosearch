# Packages
import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor

from datapunt_geosearch.blueprints import health, search
from datapunt_geosearch.db import connection_cache

# Configure OpenTelemetry to use Azure Monitor with the
# APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APPLICATIONINSIGHTS_CONNECTION_STRING is not None:
    configure_azure_monitor(logger_name="root")
    logger = logging.getLogger("root")
    logger.warning("OpenTelemetry has been enabled")


def deactivate_user_context(e):
    """Rollback the end user context on any db connections using it."""
    for conn in connection_cache.values():
        if conn._active_user:
            conn.deactivate_end_user()


def create_app(import_path: str = "datapunt_geosearch.config"):

    import flask
    from flask_cors import CORS

    app = flask.Flask("geosearch")
    CORS(app)

    app.config.from_object(import_path)
    app.register_blueprint(search.search)
    app.register_blueprint(health.health)

    app.teardown_request(deactivate_user_context)

    return app
