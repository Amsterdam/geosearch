import time
import unittest
import pytest

from datapunt_geosearch import config
from datapunt_geosearch import datasource
from datapunt_geosearch.registry import registry


@pytest.mark.usefixtures("vsd_db", "vsd_biz_data")
class TestBIZDataset(unittest.TestCase):
    def setUp(self):
        registry._datasets_initialized = time.time()
        registry.init_vsd_datasets(dsn=config.DSN_VARIOUS_SMALL_DATASETS)

    def test_query(self):
        x = 121723
        y = 486199

        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        ds = ds_class(dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        results = ds.query(x, y)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/1/$')
        self.assertEqual(display, 'Utrechtsestraat')

    def test_query_wgs84(self):
        lat = 52.36287
        lon = 4.87529

        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        ds = ds_class(dsn=config.DSN_VARIOUS_SMALL_DATASETS)
        results = ds.query(lat, lon, rd=False)

        self.assertEqual(len(results['features']), 1)
        uri = results['features'][0]['properties']['uri']
        display = results['features'][0]['properties']['display']
        self.assertRegex(uri, 'biz/2/$')
        self.assertEqual(display, 'Oud West')


if __name__ == '__main__':
    unittest.main()
