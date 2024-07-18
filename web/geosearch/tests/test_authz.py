import json
import unittest
import unittest.mock

import flask
import pytest
from flask import current_app as app


@pytest.mark.usefixtures(
    "dataservices_db",
    "create_authz_token",
    "dataservices_fake_data",
    "test_client",
    "role_configuration",
)
class AuthzTestCase(unittest.TestCase):
    def test_unauthenticated_request_returns_only_public_data(self):
        with self.client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=100&datasets=fake/public,fake/secret"
            )
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)
            self.assertEqual(json_response["features"][0]["properties"]["type"], "fake/public")

    @unittest.mock.patch("datapunt_geosearch.authz.logger")
    def test_incorrect_bearer_results_in_error(self, logger_mock):
        with self.client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=100&datasets=fake/public,fake/secret",
                headers={"Authorization": "Bearer hash"},
            )
            self.assertEqual(response.status_code, 401)
            self.assertIn("401 Unauthorized", response.data.decode("utf-8"))
            self.assertEqual(
                logger_mock.mock_calls,
                [
                    unittest.mock.call.warning(
                        "Auth problem: incorrect token. Token format unrecognized"
                    )
                ],
            )

    def test_correct_bearer_accepted_and_scopes_assigned(self):
        token = self.create_authz_token(
            subject="test@amsterdam.nl", scopes=["CA/W", "FAKE/SECRET"]
        )
        with self.client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=100&datasets=fake/public,fake/secret",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(flask.g.authz_scopes, {"CA/W", "FAKE/SECRET"})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 2)

    def test_ggd_email_accepted_and_scopes_assigned(self):
        token = self.create_authz_token(
            subject="test@ggd.amsterdam.nl", scopes=["CA/W", "FAKE/SECRET"]
        )
        with self.client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=100&datasets=fake/public,fake/secret",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(flask.g.authz_scopes, {"CA/W", "FAKE/SECRET"})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 2)

    def test_dataset_table_with_authorization_not_visible(self):
        with self.client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake_secret")
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 0)

    def test_dataset_table_with_authorization_not_visible_with_no_scope(self):
        token = self.create_authz_token(subject="test@amsterdam.nl", scopes=["CA/W", "TEST"])
        with self.client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=1&datasets=fake_secret",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(flask.g.authz_scopes, {"TEST", "CA/W"})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 0)

    def test_dataset_table_with_authorization_visible_to_authorized(self):
        token = self.create_authz_token(
            subject="test@amsterdam.nl", scopes=["CA/W", "TEST", "FAKE/SECRET"]
        )
        with app.test_client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=1&datasets=fake/secret",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(flask.g.authz_scopes, {"CA/W", "TEST", "FAKE/SECRET"})
            self.assertEqual(flask.g.token_subject, "test@amsterdam.nl")
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)
