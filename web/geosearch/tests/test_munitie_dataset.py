import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource


class TestMunitieDataset(unittest.TestCase):
    def test_query(self):
        x = 120001.1
        y = 486420.9

        ds = datasource.BominslagMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_radius_and_limit(self):
        x = 120535.2
        y = 486376.3
        radius = 600
        limit = 2

        ds = datasource.BominslagMilieuDataSource(dsn=config.DSN_MILIEU)

        results = ds.query(x, y, radius=radius)
        self.assertEqual(len(results['features']), 3)

        results = ds.query(x, y, radius=radius, limit=limit)
        self.assertEqual(len(results['features']), 2)

    def test_query_wgs84(self):
        x = 52.364559349655
        y = 4.87336380721222

        ds = datasource.BominslagMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.3641918658574
        y = 4.88121013879857
        radius = 600

        ds = datasource.BominslagMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 3)


if __name__ == '__main__':
    unittest.main()
