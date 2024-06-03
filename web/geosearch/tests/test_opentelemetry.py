from flask import current_app as app
from opentelemetry import trace

from datapunt_geosearch import db


def test_database_instrumentation(
    test_client,
):
    """Confirm that request path and trace_id are logged to database."""
    with test_client() as client:
        client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake")
        cur = db.dbconnection(
            app.config["DSN_DATASERVICES_DATASETS"], set_user_role=True
        )._conn.cursor()
        cur.execute("select;")
        assert "/*" in str(cur.query)
        assert "route='/'" in str(cur.query)
        current_span = trace.get_current_span()
        assert hex(current_span.get_span_context().trace_id)[2::] in str(cur.query)
