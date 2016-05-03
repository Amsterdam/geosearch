# Packages
from flask import Flask
from datapunt_geosearch.blueprints import search
from datapunt_geosearch.blueprints import health



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
    app.register_blueprint(search.search)

    # Registering health blueprint
    app.register_blueprint(health.health)

    return app
