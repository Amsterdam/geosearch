import json
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set

import psycopg2.extras
from flask import current_app as app
from schematools.exceptions import SchemaObjectNotFound
from schematools.loaders import get_schema_loader
from schematools.naming import to_snake_case, toCamelCase
from schematools.types import DatasetSchema, DatasetTableSchema

from datapunt_geosearch.datasource import DataSourceBase
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

_logger = logging.getLogger(__name__)

# The schema_loader depends on the value of the SCHEMA_URL env. variable
# It that is not provided, the default schema location
# `https://schemas.data.amsterdam.nl/datasets` is being used.
_schema_loader = get_schema_loader()

DEFAULT_CRS = "EPSG:28992"


class DatasetRegistry:
    """
    Dataset Registry.
    """

    # Determines the refresh interval for dynamic datasources
    INITIALIZE_DELAY_SECONDS = 300

    def __init__(self):
        # Datasets is a mapping of conn string => Datasources.
        self.datasets: Dict[str, List[DataSourceBase]] = defaultdict(list)
        self.providers: Dict[str, DataSourceBase] = dict()
        self._datasets_initialized = None

    def register_datasource(self, dsn, datasource_class):
        """Register a Datasource class with a dsn (synonymous to connection string)"""
        self.datasets[dsn].append(datasource_class)

        for dataset in datasource_class.metadata["datasets"]:
            self.providers[dataset] = datasource_class
            for table in datasource_class.metadata["datasets"][dataset]:
                key = f"{dataset}/{table}"
                if table in self.providers and self.providers[table] != datasource_class:
                    _logger.debug(
                        "Provider for {} already defined {} and will be overwritten by {}.".format(  # noqa: E501
                            table, self.providers[table], datasource_class
                        )
                    )
                self.providers[key] = datasource_class

    def register_external_dataset(self, name, base_url, path, field_mapping=None):
        from datapunt_geosearch.datasource import ExternalDataSource

        class_name = "{}ExternalDataSource".format(name.upper())

        meta = {"base_url": base_url, "datasets": {name: {name: path}}}
        if field_mapping is not None:
            meta["field_mapping"] = field_mapping

        datasource_class = type(class_name, (ExternalDataSource,), dict(metadata=meta))

        self.register_datasource("EXT_{}".format(name.upper()), datasource_class)
        return datasource_class

    def get_all_datasources(self):
        self.init_datasets()
        return self.providers

    def get_all_dataset_names(self):
        return self.get_all_datasources().keys()

    def get_by_name(self, name):
        return self.get_all_datasources().get(name)

    def filter_datasources(
        self, names: List[str], scopes: Optional[List[str]] = None
    ) -> Set[DataSourceBase]:
        """Return the datasource classes associated with
        the given datasets or tables (given by `names`).

        The result is deduplicated because it is not guaranteed that the searched keys
        return a unique set of datasources. This occurs for example when two datasets
        from hosted by the same datsource are used as search keys.
        """
        return set(
            [
                datasource_cls
                for name, datasource_cls in self.get_all_datasources().items()
                if name in names and datasource_cls.check_scopes(scopes=scopes)
            ]
        )

    def init_dataset(
        self,
        row,
        class_name,
        dsn_name,
        base_url=None,
        scopes=None,
        field_name_transformation=None,
        temporal_dimension=None,
        crs=None,
        set_user_role=False,
        dataset_field_names=None,
    ):
        """
        Initialize dataset class and register it in registry based on row data

        Args:
          row (dict): Dictionary with keys:
            - schema,
            - name,
            - name_field,
            - table_name,
            - geometry_field,
            - geometry_type,
            - id_field
            - dataset_name
            - dataset_path  (optional, for amsterdam schema datasets)
          class_name (str): Name for the new class
          dsn_name: DSN for namespacing
          scopes: Optional comma separated list of Authentication scopes for dataset.
          field_name_transformation: Optional function that will transform field names.

        Returns:
          DataSourceBase subclass for given dataset.
        """
        if field_name_transformation is None:

            def field_name_transformation(x):
                return x

        if row.get("schema") is None:
            row["schema"] = "public"
        schema_table = row["schema"] + "." + row["table_name"]

        if row["geometry_type"] and row["geometry_type"].upper() in [
            "POLYGON",
            "MULTIPOLYGON",
        ]:
            operator = "contains"
        else:
            operator = "within"

        if not all(
            [
                row["name"],
                row["name_field"],
                row["dataset_name"],
                row["geometry_field"],
                row["id_field"],
            ]
        ):
            _logger.warning(f"Incorrect dataset: {class_name}")
            return None
        name = field_name_transformation(row["name"])
        name_field = field_name_transformation(row["name_field"])
        dataset_name = field_name_transformation(row["dataset_name"])
        if dataset_name == "covid_19":
            dataset_name = "covid19"
        # Do not apply a field_name_transformation to dataset_path
        # because that could mess with the `/`.
        dataset_path = row.get("dataset_path", dataset_name)
        if dataset_path == "covid_19":
            dataset_path = "covid19"
        geometry_field = field_name_transformation(row["geometry_field"])
        id_field = field_name_transformation(row["id_field"])

        base_url = base_url or app.config["DATAPUNT_API_URL"]

        fields = [
            f"{name_field} as display",
            f"cast('{dataset_name}/{name}' as varchar(50)) as type",
            f"'{base_url}{dataset_path}/{name}/' || {id_field} || '/'  as uri",
            f"{geometry_field} as geometrie",
            f"{id_field} as id",
        ]

        temporal_bounds = None
        if temporal_dimension is not None:
            temporal_bounds = (
                field_name_transformation(temporal_dimension.start.db_name),
                field_name_transformation(temporal_dimension.end.db_name),
            )
            fields += list(temporal_bounds)

        datasource_class = type(
            class_name,
            (DataSourceBase,),
            {
                "metadata": {
                    "geofield": geometry_field,
                    "operator": operator,
                    "datasets": {dataset_name: {name: schema_table}},
                    "scopes": scopes or set(),
                    "fields": fields,
                },
                "dsn_name": dsn_name,
                "temporal_bounds": temporal_bounds,
                "dataset_field_names": dataset_field_names,
                "crs": crs,
                "set_user_role": set_user_role,
            },
        )

        self.register_datasource(dsn_name, datasource_class)
        return datasource_class

    def init_datasets(self):
        """Initialize dynamic datasources. In this case a
        Datasource class is generated for each dataset in vsd and
        in the dataservices database."""
        if (
            self._datasets_initialized is None
            or time.time() - self._datasets_initialized > self.INITIALIZE_DELAY_SECONDS
        ):
            self.init_dataservices_datasets()
            self._datasets_initialized = time.time()

    def _fetch_temporal_dimensions(self, dataset_table: DatasetTableSchema):
        temporal = dataset_table.temporal
        if temporal is None:
            return None
        return temporal.dimensions.get("geldigOp")

    def _replace_id_field_for_temporal(self, row, dataset_table):
        """For temporal datasets, we do not return the raw `id`, but only the base field.

        Usually, for temporal tables, the raw id is `identificatie`.`volgnummer`.
        Geosearch user are only interested in the `identificatie`, so we return that
        as the `id_field`.
        """
        temporal = dataset_table.temporal
        if temporal is not None:
            new_row = row.copy()  # be immutable
            identifier_base_field_name = set(dataset_table.identifier) - {temporal.identifier}
            try:
                new_row["id_field"] = next(iter(identifier_base_field_name))
            except StopIteration:
                raise RuntimeError(
                    "Table `{dataset_table.db_table}` is temporal"
                    "but does have a single `identifier`,"
                    "this is not possible."
                )
            return new_row
        return row

    def init_dataservices_datasets(self, dsn=None):
        try:
            dbconn = dbconnection(app.config["DSN_DATASERVICES_DATASETS"])
        except psycopg2.Error as e:
            _logger.error("Error creating connection: %s" % e)
            raise DataSourceException("error connecting to datasource") from e

        sql = """
    SELECT
        dt.name,
        dt.display_field as name_field,
        dt.db_table as table_name,
        dt.geometry_field_type as geometry_type,
        dt.geometry_field,
        dt.id_field as id_field,
        d.name as dataset_name,
        d.path as dataset_path,
        d.schema_data,
        d.auth as dataset_authorization,
        dt.auth as datasettable_authorization
    FROM datasets_dataset d
    LEFT JOIN datasets_datasetversion dv
      ON d.id = dv.dataset_id
    LEFT JOIN datasets_datasettable_dataset_versions dtv
      ON dv.id = dtv.datasetversion_id
    LEFT JOIN datasets_datasettable dt
      ON dt.id = dtv.datasettable_id
    WHERE d.default_version = dv.version
      AND d.enable_api = true AND dt.enable_geosearch = true
      AND d.default_version = dv.version
      AND geometry_field_type is not null
        """
        datasets = dict()
        for row in dbconn.fetch_all(sql):
            # TODO: Remove all code assuming that schema_data can be inconsistent
            crs = DEFAULT_CRS
            temporal_dimension = None
            dataset_field_names = None
            if row["schema_data"]:
                try:
                    # TODO: Remove schematools as a dependency or use a proper loader
                    # object so that relations can be resolved. Dataset* objs are not
                    # ready to be a public API.
                    # For now we use a URL schema loader that is created at module load time.
                    dataset_schema = DatasetSchema.from_dict(
                        json.loads(row["schema_data"]),
                    )
                    dataset_table = dataset_schema.get_table_by_id(
                        toCamelCase(row["name"]), include_nested=False, include_through=False
                    )
                    crs = dataset_table.main_geometry_field.crs

                    temporal_dimension = self._fetch_temporal_dimensions(dataset_table)
                    dataset_field_names = [f.db_name for f in dataset_table.fields]

                    row = self._replace_id_field_for_temporal(row, dataset_table)

                except SchemaObjectNotFound:
                    # We should be able to assume that the ams-schemas are
                    # internally consistent but there is code (tests) in this
                    # codebase making the assumption that we can create
                    # Datasources for internally inconsistent schemas (i.e. presence of
                    # tables that are not referenced by the dataset)
                    # this is a workaround.
                    _logger.warning(f"Table {row['name']} in db but not referenced by dataset")
                    continue

            scopes = set()
            if row["dataset_authorization"]:
                scopes = set(row["dataset_authorization"].split(","))
            if row["datasettable_authorization"]:
                scopes.update(set(row["datasettable_authorization"].split(",")))
            dataset = self.init_dataset(
                row=row,
                class_name=row["dataset_name"] + row["name"] + "DataservicesDataSource",
                dsn_name="DSN_DATASERVICES_DATASETS",
                base_url=f"{app.config['DATAPUNT_API_URL']}v1/",
                scopes=scopes,
                field_name_transformation=to_snake_case,
                temporal_dimension=temporal_dimension,
                crs=crs,
                # Connections to the reference database must use role switching
                # on Azure.
                set_user_role=True,
                dataset_field_names=dataset_field_names,
            )
            if dataset is not None:
                key = f"{row['dataset_name']}/{row['name']}"
                datasets[key] = dataset

        return datasets


# Initialize the registry with the statically defined Datasources
registry = DatasetRegistry()
