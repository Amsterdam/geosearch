import json
import time
import unittest
import pytest
import datapunt_geosearch
from datapunt_geosearch import config


@pytest.mark.usefixtures("dataservices_db")
class SearchEverywhereTestCase(unittest.TestCase):
    def setUp(self):
        self.app = datapunt_geosearch.create_app(config=config)

    def test_incorrect_request_results_in_error(self):
        with self.app.test_client() as client:
            response = client.get('/')
            self.assertEqual(response.data, b'{"error":"No coordinates found"}\n')

    def test_regular_request_results_in_valid_json(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=100')
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 6)

    def test_search_limited_by_subset_results_in_correct_filter(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=10&datasets=buurt')
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 1)
            self.assertEqual(json_response['features'][0]['properties']['type'], 'gebieden/buurt')

    def test_search_limited_by_dataset_results_in_correct_filter(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=1&datasets=gebieden')
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 6)
            for item in json_response['features']:
                self.assertTrue(item['properties']['type'].startswith('gebieden'))

    @pytest.mark.usefixtures("dataservices_biz_data")
    def test_search_in_dataservices_results_in_correct_result(self):
        with self.app.test_client() as client:
            response = client.get('/?x=123282.6&y=487674.8&radius=1&datasets=biz')
            json_response = json.loads(response.data)
            self.assertEqual(json_response['type'], 'FeatureCollection')
            self.assertEqual(len(json_response['features']), 1)
