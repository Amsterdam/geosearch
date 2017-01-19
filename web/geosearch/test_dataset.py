import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource

# tested running atlas_import database with latest atlas backup:
# docker-compose exec atlas_db /bin/update-db.sh atlas
# docker-compose exec nap_db /bin/update-db.sh nap
# python test_dataset.py
# > Ran 1 test in 0.062s


class TestAtlasDataset(unittest.TestCase):
    def test_query(self):
        x = 120993
        y = 485919

        ds = datasource.AtlasDataSource(dsn=config.DSN_ATLAS)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 7)

    def test_query_wgs84(self):
        x = 52.36011
        y = 4.88798

        ds = datasource.AtlasDataSource(dsn=config.DSN_ATLAS)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 7)


class TestNapDataset(unittest.TestCase):
    def test_query(self):
        x = 120535.2
        y = 486376.3

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)

    def test_query_radius(self):
        x = 120535.2
        y = 486376.3
        radius = 130

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 4)

    def test_query_wgs84(self):
        x = 52.3641918658574
        y = 4.88121013879857

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.3641918658574
        y = 4.88121013879857
        radius = 130

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 4)


class TestMinutieDataset(unittest.TestCase):
    def test_query(self):
        x = 120535.2
        y = 486376.3

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)

    def test_query_radius(self):
        x = 120535.2
        y = 486376.3
        radius = 130

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 4)

    def test_query_wgs84(self):
        x = 52.3641918658574
        y = 4.88121013879857

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.3641918658574
        y = 4.88121013879857
        radius = 130

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 4)


if __name__ == '__main__':
    unittest.main()
