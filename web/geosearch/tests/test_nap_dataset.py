import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource


class TestNapDataset(unittest.TestCase):
    def test_query(self):
        x = 120364.0
        y = 488156.3

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_radius_and_limit(self):
        x = 120364.0
        y = 488156.3
        radius = 70
        limit = 1

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)

        results = ds.query(x, y, radius=radius)
        self.assertEqual(len(results['features']), 5)

        results = ds.query(x, y, radius=radius, limit=limit)
        self.assertEqual(len(results['features']), 2)

    def test_query_wgs84(self):
        x = 52.38018
        y = 4.87851

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.38018
        y = 4.87851
        radius = 70

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 5)


if __name__ == '__main__':
    unittest.main()
