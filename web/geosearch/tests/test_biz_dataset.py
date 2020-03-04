import time
import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource
from datapunt_geosearch.registry import registry


class TestBIZDataset(unittest.TestCase):
    def setUp(self):
        registry._datasets_initialized = time.time()
        registry.init_vsd_datasets(dsn=config.DSN_VARIOUS_SMALL_DATASETS)

    def test_query(self):
        x = 121723
        y = 486199

        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        ds = ds_class(dsn=config.DSN_VARIOUS_SMALL_DATASETS)

        expected = ds.dbconn.fetch_one("""
        SELECT *
        FROM biz_view
        WHERE ST_DWithin(geometrie, ST_GeomFromText('POINT(121723 486199)', 28992), 30)
        """)

        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/{}/$'.format(expected['id']))
        self.assertEqual(display, expected['naam'])

    def test_query_wgs84(self):
        lat = 52.36287
        lon = 4.87529

        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        ds = ds_class(dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        results = ds.query(lat, lon, rd=False)

        expected = ds.dbconn.fetch_one("""
        SELECT *
        FROM biz_view
        WHERE ST_DWithin(geometrie, ST_Transform(ST_GeomFromText('POINT(4.87529 52.36287)', 4326), 28992), 30)
        """)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/{}/$'.format(expected['id']))
        self.assertEqual(display, expected['naam'])


if __name__ == '__main__':
    unittest.main()
