from flask import current_app as app

def test_cors_header(test_client):
    with test_client() as client:
        resp = client.get("/nap/?lat=52.7&lon=4.8")
        assert "Access-Control-Allow-Origin" in resp.headers
        assert resp.headers["Access-Control-Allow-Origin"] == "*"