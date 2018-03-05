import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource

# tested running bag_import database with latest bag backup:
# docker-compose exec bag_db /bin/update-db.sh bag
# docker-compose exec nap_db /bin/update-db.sh nap
# python test_dataset.py
# > Ran 1 test in 0.062s


class TestBAGDataset(unittest.TestCase):
    def test_query(self):
        x = 120993
        y = 485919

        ds = datasource.BagDataSource(dsn=config.DSN_BAG)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 7)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_wgs84(self):
        x = 52.36011
        y = 4.88798

        ds = datasource.BagDataSource(dsn=config.DSN_BAG)
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['features']), 7)


class TestNapDataset(unittest.TestCase):
    def test_query(self):
        x = 120535.2
        y = 486376.3

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_radius_and_limit(self):
        x = 120535.2
        y = 486376.3
        radius = 130
        limit = 1

        ds = datasource.NapMeetboutenDataSource(dsn=config.DSN_NAP)

        results = ds.query(x, y, radius=radius)
        self.assertEqual(len(results['features']), 4)

        results = ds.query(x, y, radius=radius, limit=limit)
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

        self.assertEqual(len(results['features']), 4)


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


class TestTellusDataset(unittest.TestCase):
    def test_query(self):
        x = 112995
        y = 485325

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        self.assertIn('distance', results['features'][0]['properties'])

    def test_query_radius(self):
        x = 112995
        y = 485325
        radius = 25000

        ds = datasource.TellusDataSource(dsn=config.DSN_TELLUS)
        results = ds.query(x, y, radius=radius)

        self.assertEqual(len(results['features']), 28)

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

        self.assertEqual(len(results['features']), 10)


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

        self.assertEqual(len(results['features']), 48)

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
        nopand = 1

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


class TestGrondExploitatieDataset(unittest.TestCase):
    def test_query(self):
        x = 130222
        y = 485753

        ds = datasource.GrondExploitatieDataSource(dsn=config.DSN_GRONDEXPLOITATIE)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        self.assertRegex(uri, 'grondexploitatie/project/26033/$')

    def test_query_wgs84(self):
        lat = 52.3748
        lon = 4.9596

        ds = datasource.GrondExploitatieDataSource(dsn=config.DSN_GRONDEXPLOITATIE)
        results = ds.query(lat, lon, rd=False)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        self.assertRegex(uri, 'grondexploitatie/project/28508/$')

class TestBIZDataset(unittest.TestCase):
    def test_query(self):
        x = 121723
        y = 486199

        ds = datasource.BIZDataSource(dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/48/$')
        self.assertEqual(display, 'Utrechtsestraat')

    def test_query_wgs84(self):
        lat = 52.36287
        lon = 4.87529

        ds = datasource.GrondExploitatieDataSource(dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        results = ds.query(lat, lon, rd=False)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/31/$')
        self.assertEqual(display, 'Oud West')

if __name__ == '__main__':
    unittest.main()
