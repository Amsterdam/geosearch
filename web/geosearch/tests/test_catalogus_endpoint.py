import json
import unittest
import unittest.mock

import flask
import pytest

from datapunt_geosearch.registry import registry


@pytest.mark.usefixtures(
    "dataservices_db", "dataservices_fake_data", "create_authz_token", "test_client"
)
class CatalogusEndpointTestCase(unittest.TestCase):
    def setUp(self):
        registry._datasets_initialized = None

    def test_authenticate_is_not_requiring_token(self):
        with self.client() as client:
            response = client.get("/catalogus/")
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertIn("datasets", json_response)

    @unittest.mock.patch("datapunt_geosearch.authz.logger")
    def test_incorrect_bearer_results_in_error(self, logger_mock):
        with self.client() as client:
            response = client.get("/catalogus/", headers={"Authorization": "Bearer hash"})
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
        token = self.create_authz_token(subject="test@test.nl", scopes=["CA/W", "TEST"])
        with self.client() as client:
            client.get("/catalogus/", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(flask.g.authz_scopes, {"CA/W", "TEST"})

    def test_dataset_table_with_authorization_not_visible(self):
        with self.client() as client:
            response = client.get("/catalogus/")
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertNotIn("fake_secret", json_response["datasets"])

    def test_dataset_table_with_authorization_not_visible_with_no_scope(self):
        token = self.create_authz_token(subject="test@test.nl", scopes=["CA/W", "TEST"])
        with self.client() as client:
            response = client.get("/catalogus/", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(flask.g.authz_scopes, {"TEST", "CA/W"})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertNotIn("fake_secret", json_response["datasets"])

    def test_dataset_table_with_authorization_visible_to_authorized(self):
        token = self.create_authz_token(
            subject="test@test.nl", scopes=["CA/W", "TEST", "FAKE/SECRET"]
        )
        with self.client() as client:
            response = client.get("/catalogus/", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(flask.g.authz_scopes, {"CA/W", "TEST", "FAKE/SECRET"})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertIn("fake/fake_secret", json_response["datasets"])


if __name__ == "__main__":
    unittest.main()
