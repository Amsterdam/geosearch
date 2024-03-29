import unittest

from flask import current_app as app

from datapunt_geosearch import datasource


class TestBAGDataset(unittest.TestCase):
    def test_query(self):
        x = 120993
        y = 485919

        ds = datasource.BagDataSource(dsn=app.config["DSN_BAG"])
        results = ds.query(x, y)

        self.assertEqual(len(results["features"]), 6)
        self.assertIn("distance", results["features"][0]["properties"])

    def test_query_wgs84(self):
        x = 52.36011
        y = 4.88798

        ds = datasource.BagDataSource(dsn=app.config["DSN_BAG"])
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results["features"]), 6)


if __name__ == "__main__":
    unittest.main()
