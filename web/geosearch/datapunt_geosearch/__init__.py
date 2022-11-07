# Packages
import os

import sentry_sdk
from flask import Flask
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

from datapunt_geosearch.blueprints import health, search
from datapunt_geosearch.db import connection_cache


def deactivate_user_context(e):
    """Rollback the end user context on any db connections using it."""
    for conn in connection_cache.values():
        if conn._active_user:
            conn.deactivate_end_user()


def create_app(import_path: str = "datapunt_geosearch.config"):
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn, environment="geosearch", integrations=[FlaskIntegration()]
        )

    app = Flask("geosearch")
    CORS(app)

    app.config.from_object(import_path)
    app.register_blueprint(search.search)
    app.register_blueprint(health.health)

    app.teardown_request(deactivate_user_context)

    return app
