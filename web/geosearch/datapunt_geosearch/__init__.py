# Packages
import os

import sentry_sdk
from flask import Flask
from flask_cors import CORS
# Project
from sentry_sdk.integrations.flask import FlaskIntegration

from datapunt_geosearch.blueprints import search
from datapunt_geosearch.blueprints import health


def create_app(config=None):
    """
    An app factory
    Possible parameter config is a python path to the config object
    """

    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment="geosearch",
            integrations=[FlaskIntegration()]
        )

    app = Flask('geosearch')
    CORS(app)

    # Config
    if config:
        app.config.from_object(config)

    # Registering search blueprint
    app.register_blueprint(search.search)

    # Registering health blueprint
    app.register_blueprint(health.health)

    return app
