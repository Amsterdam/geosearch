import json
import unittest
from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from flask import current_app as app

from datapunt_geosearch.registry import registry


@pytest.mark.usefixtures("dataservices_db")
class SearchEverywhereTestCase(unittest.TestCase):
    def test_incorrect_request_results_in_error(self):
        with app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.data, b'{"error":"No coordinates found"}\n')

    def test_regular_request_results_in_valid_json(self):
        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=100")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 2)

    def test_search_limited_by_subset_results_in_correct_filter(self):
        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=10&datasets=gebieden/buurt")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)
            self.assertEqual(json_response["features"][0]["properties"]["type"], "gebieden/buurt")

    def test_search_limited_by_dataset_results_in_correct_filter(self):
        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=gebieden")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 6)
            for item in json_response["features"]:
                self.assertTrue(item["properties"]["type"].startswith("gebieden"))

    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_results_in_correct_result(self):
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)
            self.assertIn("path/fake", json_response["features"][0]["properties"]["uri"])

    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_with_dataset_table__results_in_correct_result(self):
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake/fake_public")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)

    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_requesting_extra_fields_in_response(self):
        """Prove that extra fields that are requested for the response, are showing up."""
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=1&datasets=fake/fake_public&_fields=volgnummer"
            )
            json_response = json.loads(response.data)
            self.assertEqual(json_response["features"][0]["properties"]["volgnummer"], 1)

    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_non_existing_extra_fields_in_response(self):
        """Prove that non existing fields that are requested for the response,
        are not a problem.
        """
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=1&datasets=fake/fake_public&_fields=nonExisting"
            )
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 1)

    # @pytest.mark.usefixtures("dataservices_fake_data")
    @pytest.mark.usefixtures("dataservices_db")
    def test_search_in_dataservices_generic_non_existing_extra_fields_in_response(self):
        """Prove that non existing fields that are requested for the generic search endpoint
        are not a problem.
        """
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get("/?x=123282.6&y=487674.8&radius=100&_fields=nonExisting")
            json_response = json.loads(response.data)
            self.assertEqual(json_response["type"], "FeatureCollection")
            self.assertEqual(len(json_response["features"]), 2)

    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_requesting_camelcased_fields_in_response(self):
        """Prove that extra fields that are camelcased are returned properly."""
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        with app.test_client() as client:
            response = client.get(
                "/?x=123282.6&y=487674.8&radius=1&datasets=fake/fake_public&_fields=eindGeldigheid"
            )
            json_response = json.loads(response.data)
            self.assertEqual(json_response["features"][0]["properties"]["eindGeldigheid"], None)

    @pytest.mark.usefixtures("dataservices_fake_temporal_data_creator")
    @pytest.mark.usefixtures("dataservices_fake_data")
    def test_search_in_dataservices_using_temporal_data(self):
        """Prove that geosearch does not take inactive records into account.

        Only records that have a `geldigheid` should be included in the search result.
        """
        # Force registry to reload dataservices datasources
        registry._datasets_initialized = None

        def _years_from_today(years):
            year_date = (date.today() + relativedelta(years=years)).strftime("%Y-%m-%d")
            return f"'{year_date}'"

        # Unfortunately, these tests are unittest-style tests, so we cannot use
        # `pytest.mark.parametrize` here.
        for extra_temporal_records, count in (
            (("NULL", "NULL"), 2),
            ((_years_from_today(-2), _years_from_today(-1)), 1),
            ((_years_from_today(-2), _years_from_today(+1)), 2),
            ((_years_from_today(+1), _years_from_today(+2)), 1),
            ((_years_from_today(+1), "NULL"), 1),
            ((_years_from_today(-1), "NULL"), 2),
        ):

            with self.data_creator(*extra_temporal_records):  # type: ignore

                with app.test_client() as client:
                    response = client.get("/?x=123282.6&y=487674.8&radius=1&datasets=fake")
                    json_response = json.loads(response.data)
                    self.assertEqual(json_response["type"], "FeatureCollection")
                    self.assertEqual(len(json_response["features"]), count)
                    self.assertIn("path/fake", json_response["features"][0]["properties"]["uri"])
