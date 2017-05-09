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

        self.assertEqual(len(results['features']), 2)

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

        self.assertEqual(len(results['features']), 2)


class TestMunitieDataset(unittest.TestCase):
    def test_query(self):
        x = 120001.1
        y = 486420.9

        ds = datasource.MunitieMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)

    def test_query_radius(self):
        x = 120535.2
        y = 486376.3
        radius = 600

        ds = datasource.MunitieMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 3)

    def test_query_wgs84(self):
        x = 52.364559349655
        y = 4.87336380721222

        ds = datasource.MunitieMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.3641918658574
        y = 4.88121013879857
        radius = 600

        ds = datasource.MunitieMilieuDataSource(dsn=config.DSN_MILIEU)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 3)


class TestTellusDataset(unittest.TestCase):
    def test_query(self):
        x = 112995
        y = 485325

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)

    def test_query_radius(self):
        x = 112995
        y = 485325
        radius = 25000

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 26)

    def test_query_wgs84(self):
        x = 52.3542193
        y = 4.7706450

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 1)

    def test_query_wgs84_radius(self):
        x = 52.372239620672204
        y = 4.900848228657843
        radius = 2500

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y, rd=False, radius=radius)

        self.assertEqual(len(results['features']), 8)


class TestMonumentenDataset(unittest.TestCase):
    def test_query(self):
        x = 123476
        y = 485368

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)

    def test_query_radius(self):
        x = 112995
        y = 485325
        radius = 2500

        ds = datasource.MonumentenDataSource(dsn=config.DSN_MONUMENTEN)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 43)

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

if __name__ == '__main__':
    unittest.main()
