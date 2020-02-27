import json
import unittest

import flask
import pytest

from datapunt_geosearch import config, create_app
from datapunt_geosearch.registry import registry


@pytest.mark.usefixtures("dataservices_db")
@pytest.mark.usefixtures("dataservices_fake_data")
@pytest.mark.usefixtures("create_authz_token")
class AuthzTestCase(unittest.TestCase):
    def setUp(self):
        registry._datasets_initialized = None
        self.app = create_app(config=config)

    def test_authenticate_is_not_requiring_token(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=100')
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 6)

    def test_incorrect_bearer_results_in_error(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=100',
                                  headers={'Authorization': 'Bearer hash'})
            self.assertEqual(response.status_code, 401)
            self.assertIn('401 Unauthorized', response.data.decode('utf-8'))

    def test_correct_bearer_accepted_and_scopes_assigned(self):
        token = self.create_authz_token(subject='test@test.nl',
                                        scopes=['CA/W', 'TEST'])
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=100',
                                  headers={'Authorization': token})
            self.assertEqual(flask.g.authz_scopes, {'CA/W', 'TEST'})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 6)

    def test_dataset_table_with_authorization_not_visible(self):
        with self.app.test_client() as client:
            response = client.get(
                '/?x=123282.6&y=487674.8&radius=1&datasets=fake_secret'
            )
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 0)

    def test_dataset_table_with_authorization_not_visible_with_no_scope(self):
        token = self.create_authz_token(subject='test@test.nl',
                                        scopes=['CA/W', 'TEST'])
        with self.app.test_client() as client:
            response = client.get(
                '/?x=123282.6&y=487674.8&radius=1&datasets=fake_secret',
                headers={'Authorization': token}
            )
            self.assertEqual(flask.g.authz_scopes, {'TEST', 'CA/W'})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 0)

    def test_dataset_table_with_authorization_visible_to_authorized(self):
        token = self.create_authz_token(subject='test@test.nl',
                                        scopes=['CA/W', 'TEST', 'FAKE/SECRET'])
        with self.app.test_client() as client:
            response = client.get(
                '/?x=123282.6&y=487674.8&radius=1&datasets=fake_secret',
                headers={'Authorization': token}
            )
            self.assertEqual(
                flask.g.authz_scopes,
                {'CA/W', 'TEST', 'FAKE/SECRET'}
            )
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 1)


if __name__ == '__main__':
    unittest.main()
