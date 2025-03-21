from typing import List

from flask import g
from opentelemetry.trace import Span

# from datapunt_geosearch.blueprints import health, search
from datapunt_geosearch.db import connection_cache


def deactivate_user_context(e):
    """Rollback the end user context on any db connections using it."""
    for conn in connection_cache.values():
        if conn._active_user:
            conn.deactivate_end_user()


def response_hook(span: Span, status: str, response_headers: List):
    if span and span.is_recording() and g.get("email") is not None:
        span.set_attribute("user.AuthenticatedId", g.get("email"))


def create_app(import_path: str = "datapunt_geosearch.config"):
    import flask
    from flask_cors import CORS
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

    app = flask.Flask("geosearch")
    CORS(app)

    # FlaskInstrumentor().instrument_app(
    #     app, excluded_urls="/status/health", response_hook=response_hook
    # )
    Psycopg2Instrumentor().instrument(
        enable_commenter=True, commenter_options={"opentelemetry_values": True}
    )

    app.config.from_object(import_path)
    app.register_blueprint(search.search)
    # app.register_blueprint(health.health)

    app.teardown_request(deactivate_user_context)

    return app
