import json
import time
import unittest

import flask
from jwcrypto.jwt import JWT
import pytest

from datapunt_geosearch import authz, config, create_app
from datapunt_geosearch.registry import registry


def create_valid_token(subject, scopes):
    jwks = authz.get_keyset()
    assert len(jwks) > 0

    key = next(iter(jwks['keys']))
    now = int(time.time())

    header = {
        'alg': 'ES256',  # algorithm of the test key
        'kid': key.key_id
    }

    token = JWT(
        header=header,
        claims={
            'iat': now,
            'exp': now + 600,
            'scopes': scopes,
            'subject': subject
        })
    token.make_signed_token(key)
    return 'bearer ' + token.serialize()


@pytest.mark.usefixtures("dataservices_db")
@pytest.mark.usefixtures("dataservices_fake_data")
class AuthzTestCase(unittest.TestCase):
    def setUp(self):
        registry._datasets_initialized = None
        self.app = create_app(config=config)

    def test_authenticate_is_not_requiring_token(self):
        with self.app.test_client() as client:
            response = client.get('/catalogus/')
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertIn('datasets', json_response)

    def test_incorrect_bearer_results_in_error(self):
        with self.app.test_client() as client:
            response = client.get('/catalogus/',
                                  headers={'Authorization': 'Bearer hash'})
            self.assertEqual(response.status_code, 401)
            self.assertIn('401 Unauthorized', response.data.decode('utf-8'))

    def test_correct_bearer_accepted_and_scopes_assigned(self):
        with self.app.app_context():
            token = create_valid_token(subject='test@test.nl',
                                       scopes=['CA/W', 'TEST'])
        with self.app.test_client() as client:
            client.get('/catalogus/', headers={'Authorization': token})
            self.assertEqual(flask.g.authz_scopes, {'CA/W', 'TEST'})

    def test_dataset_table_with_authorization_not_visible(self):
        with self.app.test_client() as client:
            response = client.get(
                '/catalogus/'
            )
            self.assertEqual(flask.g.authz_scopes, None)
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertNotIn('fake_secret', json_response['datasets'])

    def test_dataset_table_with_authorization_not_visible_with_no_scope(self):
        with self.app.app_context():
            token = create_valid_token(subject='test@test.nl',
                                       scopes=['CA/W', 'TEST'])
        with self.app.test_client() as client:
            response = client.get(
                '/catalogus/',
                headers={'Authorization': token}
            )
            self.assertEqual(flask.g.authz_scopes, {'TEST', 'CA/W'})
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertNotIn('fake_secret', json_response['datasets'])

    def test_dataset_table_with_authorization_visible_to_authorized(self):
        with self.app.app_context():
            token = create_valid_token(subject='test@test.nl',
                                       scopes=['CA/W', 'TEST', 'FAKE/SECRET'])
        with self.app.test_client() as client:
            response = client.get(
                '/catalogus/',
                headers={'Authorization': token}
            )
            self.assertEqual(
                flask.g.authz_scopes,
                {'CA/W', 'TEST', 'FAKE/SECRET'}
            )
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertIn('fake_secret', json_response['datasets'])


if __name__ == '__main__':
    unittest.main()
