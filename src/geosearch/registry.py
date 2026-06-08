from schematools.contrib.django.factories import DjangoModelFactory
from schematools.contrib.django.models import Dataset, DynamicModel
from schematools.naming import to_snake_case
from schematools.types import DatasetSchema


class TableNotFoundException(Exception):
    pass


class DatasetRegistry:
    def __init__(self):
        self._datasets: dict[str, Dataset] = {}
        self._tables: dict[str, DynamicModel] = {}
        self._tables_for_scopes: dict[frozenset, list[str]] = {}
        self.is_initialized = False

    def initialize(self):
        """
        Retrieve all geosearch enabled datasets from the database and add them to the registry.
        Both the versioned and default paths are added to the registry.
        """
        datasets = [
            ds for ds in Dataset.objects.all() if ds.schema.has_an_available_geosearch_version
        ]

        for dataset in datasets:
            dataset_id = to_snake_case(dataset.schema.id)
            self._datasets[dataset_id] = dataset
            for vmajor, version in dataset.schema.versions.items():
                if not version.enable_geosearch:
                    continue
                for table in version.get_tables():
                    if table.has_geometry_fields:
                        table_id = to_snake_case(table.id)

                        factory = DjangoModelFactory(
                            dataset=dataset,
                            base_app_name="geosearch.dynamic_api",
                            base_model=DynamicModel,
                        )
                        factory.set_version(vmajor)
                        model = factory.build_model(table_schema=table)

                        if version.is_default:
                            key = f"{dataset_id}/{table_id}"
                            self._tables[key] = model

                        key = f"{dataset_id}/{vmajor}/{table_id}"
                        self._tables[key] = model

        self.is_initialized = True

    def get_table_paths(self, scopes: frozenset[str]) -> list[str]:
        if scopes in self._tables_for_scopes:
            return self._tables_for_scopes[scopes]

        all_paths = []
        for dataset_id, dataset in self._datasets.items():
            filtered_dataset = DatasetSchema.filter_on_scopes(dataset.schema, list(scopes))
            for vmajor, version in filtered_dataset.versions.items():
                if not version.enable_geosearch:
                    continue
                for table in version.get_tables():
                    if table.has_geometry_fields:
                        table_id = to_snake_case(table.id)

                        if version.is_default:
                            all_paths.append(f"{dataset_id}/{table.id}")

                        all_paths.append(f"{dataset_id}/{vmajor}/{table_id}")

        # Cache the tables for the given scope
        self._tables_for_scopes[scopes] = all_paths

        return all_paths

    def get_table_by_path(self, path: str) -> DynamicModel:
        try:
            return self._tables[path]
        except KeyError as e:
            raise TableNotFoundException from e

    def get_tables_by_path(self, path: str = "") -> dict[str, DynamicModel]:
        if "/" not in path:
            # The whole dataset was requested, return all default tables for the dataset
            return {
                key: table
                for key, table in self._tables.items()
                if key.startswith(path) and not key.count("/") > 1
            }
        return {path: self.get_table_by_path(path)}


_registry = DatasetRegistry()


def get_registry() -> DatasetRegistry:
    if not _registry.is_initialized:
        _registry.initialize()
    return _registry
