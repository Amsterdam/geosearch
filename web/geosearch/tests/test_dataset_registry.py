import time
import unittest
import unittest.mock

from datapunt_geosearch import config
from datapunt_geosearch import datasource
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.registry import registry, DatasetRegistry


class TestDatasetRegistry(unittest.TestCase):
    def test_biz_class_registered_in_registry(self):
        ds_class = datasource.get_dataset_class('biz', dsn=config.DSN_VARIOUS_SMALL_DATASETS)

        self.assertEqual(registry.providers['biz'], ds_class)

    def test_dataset_is_registered_for_each_dataset_in_metadata(self):
        class TestDataset:
            metadata = {
                'datasets': {
                    'magic': {
                        'test1': [],
                        'test2': []
                    }
                }
            }
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset('DSN_TEST_DATASET', TestDataset)

        self.assertEqual(test_registry.get_all_datasets(), {
            'magic': TestDataset,
            'test1': TestDataset,
            'test2': TestDataset
        })

    def test_init_dataset_creates_dataset_class(self):
        row = dict(
            schema='test',
            table_name='test_table',
            name='test_name',
            name_field='description',
            geometry_type='POLYGON',
            geometry_field='geometry',
            id_field='id',
        )
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        result = test_registry.init_dataset(row, 'TestDataset', 'DSN_TEST_DATASET')

        self.assertTrue(issubclass(result, datasource.DataSourceBase))
        self.assertEqual(result.metadata['geofield'], row['geometry_field'])
        self.assertEqual(result.metadata['datasets'], {'vsd': {'test_name': 'test.test_table'}})
        self.assertEqual(result.metadata['fields'][0], "description as display")
        self.assertEqual(result.metadata['fields'][1], "cast('vsd/test_name' as varchar(30)) as type")
        self.assertEqual(
            result.metadata['fields'][2],
            "'https://api.data.amsterdam.nl/vsd/test_name/' || id || '/'  as uri",
        )
        self.assertEqual(result.metadata['fields'][3], "geometry as geometrie")
        self.assertEqual(result.metadata['fields'][4], "id as id")
        self.assertEqual(
            test_registry.providers,
            dict(
                vsd=result,
                test_name=result,
            )
        )

    def test_init_dataset_defaults_schema_to_public(self):
        row = dict(
            schema=None,
            table_name='test_table',
            name='test_name',
            name_field='description',
            geometry_type='POLYGON',
            geometry_field='geometry',
            id_field='id',
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, 'TestDataset', 'DSN_TEST_DATASET')

        self.assertEqual(result.metadata['datasets'], {'vsd': {'test_name': 'public.test_table'}})

    def test_init_dataset_defaults_operator_to_within(self):
        row = dict(
            schema=None,
            table_name='test_table',
            name='test_name',
            name_field='description',
            geometry_type='POINT',
            geometry_field='geometry',
            id_field='id',
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, 'TestDataset', 'DSN_TEST_DATASET')

        self.assertEqual(result.metadata['operator'], 'within')

    def test_init_dataset_sets_operator_to_contains_for_polygons(self):
        row = dict(
            schema=None,
            table_name='test_table',
            name='test_name',
            name_field='description',
            geometry_type='POLYGON',
            geometry_field='geometry',
            id_field='id',
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, 'TestDataset', 'DSN_TEST_DATASET')

        self.assertEqual(result.metadata['operator'], 'contains')

    def test_init_vsd_datasets_calling_init_dataset_for_each_catalog(self):
        registry = DatasetRegistry()
        registry.init_dataset = unittest.mock.MagicMock()
        registry.init_vsd_datasets(dsn=config.DSN_VARIOUS_SMALL_DATASETS)

        dbconn = dbconnection(config.DSN_VARIOUS_SMALL_DATASETS)

        datasets = dbconn.fetch_dict("SELECT * FROM cat_dataset WHERE enable_geosearch = true")

        self.assertEqual(len(registry.init_dataset.mock_calls), len(datasets))
        for row in datasets:
            self.assertIn(
                unittest.mock.call(
                    row=unittest.mock.ANY,
                    class_name=row['name'].upper() + 'GenAPIDataSource',
                    dsn_name='DSN_VARIOUS_SMALL_DATASETS'
                ),
                registry.init_dataset.mock_calls,
            )

    def test_filter_datasets(self):
        class TestDataset:
            metadata = {
                'datasets': {
                    'magic': {
                        'test1': [],
                        'test2': []
                    }
                }
            }
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset('DSN_TEST_DATASET', TestDataset)

        self.assertEqual(test_registry.filter_datasets(names=['test1']), {TestDataset})


if __name__ == '__main__':
    unittest.main()
