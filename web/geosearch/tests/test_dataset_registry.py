import time
import unittest
import unittest.mock

from datapunt_geosearch import config
from datapunt_geosearch import datasource
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.datasource import DataSourceBase
from datapunt_geosearch.registry import registry, DatasetRegistry


class TestDatasetRegistry(unittest.TestCase):
    def test_biz_class_registered_in_registry(self):
        ds_class = datasource.get_dataset_class(
            "biz", dsn=config.DSN_VARIOUS_SMALL_DATASETS
        )

        self.assertEqual(registry.providers["biz"], ds_class)

    def test_dataset_is_registered_for_each_dataset_in_metadata(self):
        class TestDataset(DataSourceBase):
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(
            test_registry.get_all_datasets(),
            {"magic": TestDataset, "test1": TestDataset, "test2": TestDataset},
        )

    def test_init_dataset_creates_dataset_class(self):
        row = dict(
            schema="test",
            table_name="test_table",
            name="test_name",
            name_field="description",
            geometry_type="POLYGON",
            geometry_field="geometry",
            id_field="id",
            dataset_name="vsd",
        )
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertTrue(issubclass(result, datasource.DataSourceBase))
        self.assertEqual(result.metadata["geofield"], row["geometry_field"])
        self.assertEqual(
            result.metadata["datasets"], {"vsd": {"test_name": "test.test_table"}}
        )
        self.assertEqual(result.metadata["fields"][0], "description as display")
        self.assertEqual(
            result.metadata["fields"][1], "cast('vsd/test_name' as varchar(30)) as type"
        )
        self.assertEqual(
            result.metadata["fields"][2],
            "'https://api.data.amsterdam.nl/vsd/test_name/' || id || '/'  as uri",
        )
        self.assertEqual(result.metadata["fields"][3], "geometry as geometrie")
        self.assertEqual(result.metadata["fields"][4], "id as id")
        self.assertEqual(test_registry.providers, dict(vsd=result, test_name=result,))

    def test_init_dataset_defaults_schema_to_public(self):
        row = dict(
            schema=None,
            table_name="test_table",
            name="test_name",
            name_field="description",
            geometry_type="POLYGON",
            geometry_field="geometry",
            id_field="id",
            dataset_name="vsd",
            dataset_authorization=None,
            datasettable_authorization=None
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertEqual(
            result.metadata["datasets"], {"vsd": {"test_name": "public.test_table"}}
        )

    def test_init_dataset_defaults_operator_to_within(self):
        row = dict(
            schema=None,
            table_name="test_table",
            name="test_name",
            name_field="description",
            geometry_type="POINT",
            geometry_field="geometry",
            id_field="id",
            dataset_name="vsd",
            dataset_authorization=None,
            datasettable_authorization=None
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertEqual(result.metadata["operator"], "within")

    def test_init_dataset_sets_operator_to_contains_for_polygons(self):
        row = dict(
            schema=None,
            table_name="test_table",
            name="test_name",
            name_field="description",
            geometry_type="POLYGON",
            geometry_field="geometry",
            id_field="id",
            dataset_name="vsd",
            dataset_authorization=None,
            datasettable_authorization=None
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertEqual(result.metadata["operator"], "contains")

    def test_init_vsd_datasets_calling_init_dataset_for_each_catalog(self):
        registry = DatasetRegistry()
        registry.init_dataset = unittest.mock.MagicMock()
        registry.init_vsd_datasets(dsn=config.DSN_VARIOUS_SMALL_DATASETS)

        dbconn = dbconnection(config.DSN_VARIOUS_SMALL_DATASETS)

        datasets = dbconn.fetch_all(
            "SELECT * FROM cat_dataset WHERE enable_geosearch = true"
        )

        self.assertEqual(len(registry.init_dataset.mock_calls), len(datasets))
        for row in datasets:
            self.assertIn(
                unittest.mock.call(
                    row=unittest.mock.ANY,
                    class_name=row["name"].upper() + "GenAPIDataSource",
                    dsn_name="DSN_VARIOUS_SMALL_DATASETS",
                ),
                registry.init_dataset.mock_calls,
            )

    def test_filter_datasets(self):
        class TestDataset(DataSourceBase):
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(test_registry.filter_datasets(names=["test1"]), {TestDataset})

    def test_filter_datasets_with_scopes_no_scope_provided(self):
        class TestDataset(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"}
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(test_registry.filter_datasets(names=["test1"]), set())

    def test_filter_datasets_with_scopes_incorrect_scope_provided(self):
        class TestDataset(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"}
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(
            test_registry.filter_datasets(names=["test1"],
                                          scopes=["TEST/READ"]),
            set()
        )

    def test_filter_datasets_with_scopes_correct_scope_provided(self):
        class TestDataset(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"}
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_dataset("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(
            test_registry.filter_datasets(names=["test1"],
                                          scopes=["TEST/WRITE"]),
            {TestDataset}
        )

    def test_init_dataservices_dataset(self):
        with unittest.mock.patch(
            "datapunt_geosearch.db._DBConnection.fetch_all"
        ) as fetch_all_mock:
            fetch_all_mock.return_value = [
                dict(
                    schema=None,
                    table_name="test_table",
                    name="test_name",
                    name_field="description",
                    geometry_field="geometry",
                    geometry_type="Point",
                    id_field="id",
                    dataset_name="test_dataset",
                    dataset_authorization=None,
                    datasettable_authorization=None
                )
            ]

            test_registry = DatasetRegistry()
            test_registry._datasets_initialized = time.time()
            datasets = test_registry.init_dataservices_datasets()

            self.assertEqual(len(datasets.keys()), 1)
            self.assertEqual(
                test_registry.providers,
                dict(
                    test_dataset=datasets["test_name"], test_name=datasets["test_name"]
                ),
            )

    def test_init_dataservices_dataset_with_authorizations(self):
        with unittest.mock.patch(
            "datapunt_geosearch.db._DBConnection.fetch_all"
        ) as fetch_all_mock:
            fetch_all_mock.return_value = [
                dict(
                    schema=None,
                    table_name="test_table",
                    name="test_name",
                    name_field="description",
                    geometry_field="geometry",
                    geometry_type="Point",
                    id_field="id",
                    dataset_name="test_dataset",
                    dataset_authorization="TEST,TEST/1",
                    datasettable_authorization="TEST,TEST/2"
                )
            ]

            test_registry = DatasetRegistry()
            test_registry._datasets_initialized = time.time()
            datasets = test_registry.init_dataservices_datasets()

            self.assertEqual(len(datasets.keys()), 1)
            self.assertEqual(
                test_registry.providers["test_dataset"].metadata["scopes"],
                {"TEST", "TEST/1", "TEST/2"}
            )

    def test_registry_will_create_debug_log_when_overriding_providers(self):
        class TestDataset:
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        fake_provider = unittest.mock.MagicMock()
        test_registry.providers["test1"] = fake_provider

        with unittest.mock.patch("datapunt_geosearch.registry._logger") as logger_mock:
            test_registry.register_dataset("DSN_TEST", TestDataset)

        self.assertEqual(
            logger_mock.mock_calls,
            [
                unittest.mock.call.debug(
                    "Provider for test1 already defined {} and will be overwritten by {}.".format(
                        fake_provider, TestDataset
                    )
                )
            ],
        )

    def test_register_external_dataset_registers_dataset(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(name="test",
                                                         base_url="http://localhost:8000",
                                                         path="test/search/")

        self.assertEqual(test_registry.datasets["EXT_TEST"], [result])
        self.assertEqual(test_registry.providers["test"], result)

    def test_register_external_dataset_creates_generator_for_external_datasource(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(name="test",
                                                         base_url="http://localhost:8000",
                                                         path="test/search/")

        instance = result()
        self.assertTrue(isinstance(instance, datasource.ExternalDataSource))

    def test_register_external_dataset_respects_field_mappring(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(
            name="test",
            base_url="http://localhost:8000",
            path="test/search/",
            field_mapping=dict(id="test")
        )

        self.assertEqual(result.metadata["field_mapping"], dict(id="test"))


if __name__ == "__main__":
    unittest.main()
