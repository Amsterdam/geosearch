import datetime
import json
import unittest
import unittest.mock

from flask import current_app as app
from datapunt_geosearch.registry import registry


class HealthTestCase(unittest.TestCase):
    def test_system_status(self):
        # Simulate that registry initiation happened 10 seconds ago.
        registry._datasets_initialized = (datetime.datetime.now() - datetime.timedelta(seconds=100)).timestamp()
        with app.test_client() as client:
            response = client.get('/status')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertEqual(int(json_response['Time since last refresh']), 100)
            self.assertEqual(json_response['Datasets initialized'], registry._datasets_initialized)
            self.assertEqual(json_response['Delay'], registry.INITIALIZE_DELAY_SECONDS)

    def test_force_refresh(self):
        # Simulate that registry initiation happened 10 seconds ago.
        registry._datasets_initialized = (datetime.datetime.now() - datetime.timedelta(seconds=100)).timestamp()
        with app.test_client() as client:
            response = client.get('/status/force-refresh')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.data)
            self.assertLess(int(json_response['Time since last refresh']), 5)
            self.assertEqual(json_response['Datasets initialized'], registry._datasets_initialized)
            self.assertEqual(json_response['Delay'], registry.INITIALIZE_DELAY_SECONDS)
