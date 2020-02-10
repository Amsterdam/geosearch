import unittest

from datapunt_geosearch import config
from datapunt_geosearch import datasource
from datapunt_geosearch.registry import registry


class TestDatasetRegistry(unittest.TestCase):
    def test_biz_class_registered_in_registry(self):
        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)

        self.assertEqual(registry.providers['biz'], ds_class)


if __name__ == '__main__':
    unittest.main()
