import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource


class TestMonumentenDataset(unittest.TestCase):
    def test_query(self):
        x = 123476
        y = 485368

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_radius(self):
        x = 112995
        y = 485325
        radius = 2500
        limit = 4

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)

        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 50)

        results = ds.query(x, y, radius=radius, limit=limit)
        self.assertEqual(len(results['features']), 4)

    def test_query_wgs84(self):
        x = 52.3553072
        y = 4.9244779

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.372239620672204
        y = 4.900848228657843
        radius = 250

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 529)

    def test_query_nopand(self):
        x = 52.3620372560367
        y = 4.95020269748781
        radius = 200

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y, rd=False, radius=radius, monumenttype='isnot_pand_bouwblok')

        self.assertEqual(len(results['features']), 1)

    def test_query_pand(self):
        x = 52.3620372560367
        y = 4.95020269748781
        radius = 200

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 3)


if __name__ == '__main__':
    unittest.main()
