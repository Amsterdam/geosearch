import time
import unittest
import unittest.mock

from datapunt_geosearch import datasource
from datapunt_geosearch.datasource import DataSourceBase
from datapunt_geosearch.registry import DatasetRegistry


class TestDatasetRegistry(unittest.TestCase):
    def test_dataset_is_registered_for_each_dataset_in_metadata(self):
        class TestDataset(DataSourceBase):
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_datasource("DSN_TEST_DATASET", TestDataset)

        self.assertEqual(
            test_registry.get_all_datasources(),
            {
                "magic": TestDataset,
                "magic/test1": TestDataset,
                "magic/test2": TestDataset,
            },
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

        self.assertTrue(issubclass(result, DataSourceBase))
        self.assertEqual(result.metadata["geofield"], row["geometry_field"])
        self.assertEqual(result.metadata["datasets"], {"vsd": {"test_name": "test.test_table"}})
        self.assertEqual(result.metadata["fields"][0], "description as display")
        self.assertEqual(
            result.metadata["fields"][1], "cast('vsd/test_name' as varchar(50)) as type"
        )
        self.assertEqual(
            result.metadata["fields"][2],
            "'https://api.data.amsterdam.nl/vsd/test_name/' || id || '/'  as uri",
        )
        self.assertEqual(result.metadata["fields"][3], "geometry as geometrie")
        self.assertEqual(result.metadata["fields"][4], "id as id")
        self.assertEqual(test_registry.providers, {"vsd": result, "vsd/test_name": result})

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
            datasettable_authorization=None,
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertEqual(result.metadata["datasets"], {"vsd": {"test_name": "public.test_table"}})

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
            datasettable_authorization=None,
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
            datasettable_authorization=None,
        )
        test_registry = DatasetRegistry()
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET")

        self.assertEqual(result.metadata["operator"], "contains")

    def test_filter_datasources(self):
        class TestDataSource(DataSourceBase):
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_datasource("DSN_TEST_DATASET", TestDataSource)

        self.assertEqual(test_registry.filter_datasources(names=["magic/test1"]), {TestDataSource})

    def test_filter_datasources_with_scopes_no_scope_provided(self):
        class TestDataSource(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"},
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_datasource("DSN_TEST_DATASET", TestDataSource)

        self.assertEqual(test_registry.filter_datasources(names=["test1"]), set())

    def test_filter_datasources_with_scopes_incorrect_scope_provided(self):
        class TestDataSource(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"},
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_datasource("DSN_TEST_DATASET", TestDataSource)

        self.assertEqual(
            test_registry.filter_datasources(names=["test1"], scopes=["TEST/READ"]),
            set(),
        )

    def test_filter_datasources_with_scopes_correct_scope_provided(self):
        class TestDataSource(DataSourceBase):
            metadata = {
                "datasets": {"magic": {"test1": [], "test2": []}},
                "scopes": {"TEST/WRITE"},
            }

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        test_registry.register_datasource("DSN_TEST_DATASET", TestDataSource)

        self.assertEqual(
            test_registry.filter_datasources(names=["magic/test1"], scopes=["TEST/WRITE"]),
            {TestDataSource},
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
                    dataset_path="test_schema/test_dataset",
                    schema_data=None,
                    dataset_authorization=None,
                    datasettable_authorization=None,
                )
            ]

            test_registry = DatasetRegistry()
            test_registry._datasets_initialized = time.time()
            datasets = test_registry.init_dataservices_datasets()

            self.assertEqual(len(datasets.keys()), 1)
            self.assertEqual(
                test_registry.providers,
                {
                    "test_dataset": datasets["test_dataset/test_name"],
                    "test_dataset/test_name": datasets["test_dataset/test_name"],
                },
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
                    dataset_path="test_schema/test_dataset",
                    schema_data=None,
                    dataset_authorization="TEST,TEST/1",
                    datasettable_authorization="TEST,TEST/2",
                )
            ]

            test_registry = DatasetRegistry()
            test_registry._datasets_initialized = time.time()
            datasets = test_registry.init_dataservices_datasets()

            self.assertEqual(len(datasets.keys()), 1)
            self.assertEqual(
                test_registry.providers["test_dataset"].metadata["scopes"],
                {"TEST", "TEST/1", "TEST/2"},
            )

    def test_registry_will_create_debug_log_when_overriding_providers(self):
        class TestDataset:
            metadata = {"datasets": {"magic": {"test1": [], "test2": []}}}

        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        fake_provider = unittest.mock.MagicMock()
        test_registry.providers["test1"] = fake_provider

        with unittest.mock.patch("datapunt_geosearch.registry._logger") as logger_mock:
            test_registry.register_datasource("DSN_TEST", TestDataset)

        self.assertEqual(
            logger_mock.mock_calls,
            [
                unittest.mock.call.debug(
                    "Provider for test1 already defined {} and will be overwritten by {}.".format(  # noqa: E501
                        fake_provider, TestDataset
                    )
                )
            ],
        )

    def test_register_external_dataset_registers_dataset(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(
            name="test", base_url="http://localhost:8000", path="test/search/"
        )

        self.assertEqual(test_registry.datasets["EXT_TEST"], [result])
        self.assertEqual(test_registry.providers["test"], result)

    def test_register_external_dataset_creates_generator_for_external_datasource(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(
            name="test", base_url="http://localhost:8000", path="test/search/"
        )

        instance = result()
        self.assertTrue(isinstance(instance, datasource.ExternalDataSource))

    def test_register_external_dataset_respects_field_mappring(self):
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()

        result = test_registry.register_external_dataset(
            name="test",
            base_url="http://localhost:8000",
            path="test/search/",
            field_mapping=dict(id="test"),
        )

        self.assertEqual(result.metadata["field_mapping"], dict(id="test"))


if __name__ == "__main__":
    unittest.main()
