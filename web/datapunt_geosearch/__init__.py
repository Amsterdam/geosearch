# Packages
from flask import Flask
from datapunt_geosearch.blueprints.search import search


def create_app(config=None):
    """
    An app factory
    Possible parameter config is a python path to the config object
    """
    app = Flask('geosearch')
    # Config
    if config:
        app.config.from_object(config)
    # Registering search blueprint
    app.register_blueprint(search)

    return app

