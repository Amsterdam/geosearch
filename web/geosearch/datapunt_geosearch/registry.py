import json
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set

import psycopg2.extras
from flask import current_app as app
from schematools.exceptions import SchemaObjectNotFound
from schematools.types import DatasetSchema, DatasetTableSchema
from schematools.utils import to_snake_case

from datapunt_geosearch.datasource import (
    BagDataSource,
    BominslagMilieuDataSource,
    DataSourceBase,
    MonumentenDataSource,
    MunitieMilieuDataSource,
    NapMeetboutenDataSource,
)
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

_logger = logging.getLogger(__name__)


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
                if (
                    table in self.providers
                    and self.providers[table] != datasource_class
                ):
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
            _logger.warn(f"Incorrect dataset: {class_name}")
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
                field_name_transformation(temporal_dimension.start),
                field_name_transformation(temporal_dimension.end),
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
                "crs": crs,
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
            # self.init_vsd_datasets()
            self.init_dataservices_datasets()
            self._datasets_initialized = time.time()

    def init_vsd_datasets(self, dsn=None):
        """
        Initialize datasets for all Various Small Datasets.
        Returns dict with datasets created.
        """
        if dsn is None:
            dsn = app.config["DSN_VARIOUS_SMALL_DATASETS"]
        try:
            dbconn = dbconnection(dsn)
        except psycopg2.Error as e:
            _logger.error("Error creating connection: %s" % e)
            raise DataSourceException("error connecting to datasource") from e

        sql = """
    SELECT
        name,
        name_field,
        schema,
        table_name,
        geometry_type,
        geometry_field,
        pk_field as id_field,
        'vsd' as dataset_name
    FROM cat_dataset
    WHERE enable_geosearch = true
        """
        datasets = dict()
        for row in dbconn.fetch_all(sql):
            dataset = self.init_dataset(
                row=row,
                class_name=row["name"].upper() + "GenAPIDataSource",
                dsn_name="DSN_VARIOUS_SMALL_DATASETS",
                base_url=f"{app.config['DATAPUNT_API_URL']}",
            )
            if dataset is not None:
                datasets[row["name"]] = dataset

        return datasets

    def _fetch_temporal_dimensions(self, dataset_table):
        temporal = dataset_table.temporal
        if temporal is None:
            return None
        return temporal.dimensions.get("geldigOp")

    def _fetch_crs(self, dataset_table: DatasetTableSchema, geo_field: Optional[str]):
        # TODO: Move this to schematools
        if geo_field:
            try:
                field = dataset_table.get_field_by_id(to_snake_case(geo_field))
                return field.data.get(
                    "crs",
                    dataset_table.data.get("crs", dataset_table.dataset.data["crs"]),
                )
            except SchemaObjectNotFound:
                pass
        return "EPSG:28992"

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
        'id' as id_field,
        d.name as dataset_name,
        d.path as dataset_path,
        d.schema_data,
        d.auth as dataset_authorization,
        dt.auth as datasettable_authorization
    FROM datasets_datasettable dt
    LEFT JOIN datasets_dataset d
      ON dt.dataset_id = d.id
    WHERE d.enable_api = true AND dt.enable_geosearch = true
        """
        datasets = dict()
        for row in dbconn.fetch_all(sql):
            dataset_schema = DatasetSchema.from_dict(json.loads(row["schema_data"]))
            dataset_table = dataset_schema.get_table_by_id(row["name"])
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
                field_name_transformation=lambda field_id: to_snake_case(field_id),
                temporal_dimension=self._fetch_temporal_dimensions(dataset_table),
                crs=self._fetch_crs(dataset_table, row["geometry_field"]),
            )
            if dataset is not None:
                key = f"{row['dataset_name']}/{row['name']}"
                datasets[key] = dataset

        return datasets


# Initialize the registry with the statically defined Datasources
registry = DatasetRegistry()

registry.register_datasource("DSN_BAG", BagDataSource)
registry.register_datasource("DSN_NAP", NapMeetboutenDataSource)
registry.register_datasource("DSN_MUNITIE", MunitieMilieuDataSource)
registry.register_datasource("DSN_MUNITIE", BominslagMilieuDataSource)
registry.register_datasource("DSN_MONUMENTEN", MonumentenDataSource)
