# Packages
import os

import sentry_sdk
from flask import Flask
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

from datapunt_geosearch.blueprints import search, health


def create_app(import_path: str = "datapunt_geosearch.config"):
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment="geosearch",
            integrations=[FlaskIntegration()]
        )

    app = Flask('geosearch')
    CORS(app)

    app.config.from_object(import_path)
    app.register_blueprint(search.search)
    app.register_blueprint(health.health)

    return app
