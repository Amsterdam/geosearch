import time
import unittest
import unittest.mock
from urllib.parse import urljoin

from requests.exceptions import HTTPError

from datapunt_geosearch import datasource
from datapunt_geosearch.registry import DatasetRegistry


class TestExternalDataSource(unittest.TestCase):
    def test_execute_applies_dataset_filtering(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        test_datasource.x = 129569.4
        test_datasource.y = 479968.42

        with unittest.mock.patch("datapunt_geosearch.datasource.ExternalDataSource.fetch_data") as fetch_mock:
            result = test_datasource.execute_queries(datasets=["google"])

        self.assertEqual(result, [])
        self.assertEqual(fetch_mock.mock_calls, [])

    def test_execute_queries_bypasses_x_and_y(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        test_datasource.x = 129569.4
        test_datasource.y = 479968.42

        with unittest.mock.patch("datapunt_geosearch.datasource.ExternalDataSource.fetch_data") as fetch_mock:
            fetch_mock.return_value = []

            test_datasource.execute_queries()

        self.assertEqual(fetch_mock.mock_calls, [unittest.mock.call(
            dataset_name="test/test", subset_url="test/geosearch/", request_params=dict(x=129569.4, y=479968.42)
        )])

    def test_execute_queries_bypasses_limit_if_set(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        test_datasource.x = 129569.4
        test_datasource.y = 479968.42
        test_datasource.limit = 1000

        with unittest.mock.patch("datapunt_geosearch.datasource.ExternalDataSource.fetch_data") as fetch_mock:
            fetch_mock.return_value = []

            test_datasource.execute_queries()

        self.assertEqual(fetch_mock.mock_calls, [unittest.mock.call(
            dataset_name="test/test",
            subset_url="test/geosearch/",
            request_params=dict(x=129569.4, y=479968.42, limit=1000)
        )])

    def test_execute_queries_bypasses_radius_if_set(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        test_datasource.x = 129569.4
        test_datasource.y = 479968.42
        test_datasource.limit = 1000
        test_datasource.radius = 30

        with unittest.mock.patch("datapunt_geosearch.datasource.ExternalDataSource.fetch_data") as fetch_mock:
            fetch_mock.return_value = []

            test_datasource.execute_queries()

        self.assertEqual(fetch_mock.mock_calls, [unittest.mock.call(
            dataset_name="test/test",
            subset_url="test/geosearch/",
            request_params=dict(x=129569.4, y=479968.42, limit=1000, radius=30)
        )])

    def test_fetch_data_formats_search_url_using_base_url(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        request_params = dict(x=129569.4, y=479968.42)

        with unittest.mock.patch("requests.get") as requests_mock:
            response_mock = unittest.mock.MagicMock()
            response_mock.json = lambda: [{"id": "31"}]
            requests_mock.return_value = response_mock

            result = test_datasource.fetch_data(
                dataset_name="test/test",
                subset_url="test/search",
                request_params=request_params
            )

        self.assertEqual(result, [{"properties": {"id": "31", "type": "test/test"}}])
        self.assertEqual(requests_mock.mock_calls, [unittest.mock.call(
            "http://localhost:8000/test/search", params=request_params, timeout=1
        )])

    def test_fetch_data_will_return_empty_result_on_error(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
        ))

        request_params = dict(x=129569.4, y=479968.42)

        with unittest.mock.patch("datapunt_geosearch.datasource._logger") as logger_mock:
            with unittest.mock.patch("requests.get") as requests_mock:
                requests_mock.side_effect = HTTPError('meh.')

                result = test_datasource.fetch_data(
                    dataset_name="test/test",
                    subset_url="test/search",
                    request_params=request_params
                )

        self.assertEqual(result, [])
        self.assertEqual(logger_mock.mock_calls, [unittest.mock.call.warning(
            "Failed to fetch data from http://localhost:8000/test/search. Error 'meh.'."
        )])

    def test_format_result_applies_field_mapping(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000/",
            datasets=dict(test=dict(test="test/geosearch/")),
            field_mapping=dict(
                display=lambda _, item: f"Test {item['id']}",
                uri=lambda base_url, item: urljoin(base_url, item['_links']['self']['href'])
            )
        ))

        result = test_datasource.format_result(dataset_name='test/test', result=[{
            "_links": {
                "self": {
                    "href": "/test/test/129569479969/"
                }
            },
            "id": "129569479969",
            "geometrie": {
                "type": "MultiPolygon",
                "coordinates": []
            }
        }])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["properties"]["id"], "129569479969")
        self.assertEqual(result[0]["properties"]["display"], "Test 129569479969")
        self.assertEqual(result[0]["properties"]["uri"], "http://localhost:8000/test/test/129569479969/")

    def test_format_result_not_breaking_when_incorrect_field_mapping_set(self):
        test_datasource = datasource.ExternalDataSource(meta=dict(
            base_url="http://localhost:8000",
            datasets=dict(test=dict(test="test/geosearch/")),
            field_mapping=dict(
                display=lambda _, item: f"Test {item['id']}",
                uri=lambda _, item: f"{item['wrong_key']}"
            )
        ))

        with unittest.mock.patch("datapunt_geosearch.datasource._logger") as logger_mock:
            result = test_datasource.format_result(dataset_name='test/test', result=[{
                "id": "129569479969",
            }])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["properties"]["id"], "129569479969")
        self.assertEqual(result[0]["properties"]["display"], "Test 129569479969")
        self.assertFalse("uri" in result[0]["properties"].keys())
        self.assertEqual(logger_mock.mock_calls, [
            unittest.mock.call.error(
                "Incorrect format template: uri in test/test. Error: 'wrong_key'."
            )
        ])

    def test_external_datasource_can_be_registered_in_registry(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        test_datasource = test_registry.register_external_dataset(
            name="test",
            base_url="http://localhost:8000",
            path="test/geosearch/"
        )

        self.assertEqual(test_registry.providers, {
            "test": test_datasource,
            "test/test": test_datasource,
        })
