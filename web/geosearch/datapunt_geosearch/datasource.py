import logging
import urllib.parse
from typing import Dict

import psycopg2.extras
import requests
from psycopg2 import sql
from schematools.naming import toCamelCase

from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

_logger = logging.getLogger(__name__)


class DataSourceBase:
    """
    Base class for querying geo spatial datasets
    """

    db = None
    dsn = None
    dataset = None
    # opr_type = openbare_ruimte_type. Water, Weg, Terrein...
    default_properties = ("id", "display", "type", "uri", "opr_type", "distance")
    radius = 30
    limit = None
    # Generic Meta for all instances of this DataSource
    metadata = {}
    temporal_bounds = None
    dataset_field_names = None
    crs = None
    # Instance specific data
    meta = None
    use_rd = True
    x = None
    y = None
    fields = "*"
    extra_where = ""
    field_names_in_query = None
    # whether the db connection should switch end user context for querying
    set_user_role = False

    def __init__(self, dsn=None, connection=None):
        _logger.debug("Creating DataSource: %s" % self.__class__.__name__)

        if not dsn and connection is None:
            raise ValueError("dsn needs to be defined")

        if connection is None:
            try:
                self.dbconn = dbconnection(dsn, set_user_role=self.set_user_role)
            except psycopg2.Error as e:
                _logger.error("Error creating connection: %s" % e)
                raise DataSourceException("error connecting to datasource") from e
        else:
            self.dbconn = connection

        # why FGS a shallow copy?
        self.meta = self.metadata.copy()

    @property
    def extra_field_names(self):
        """Return the extra fields in the geosearch output.

        The fieldnames that are possible because of the fields in de dataset
        are configured in the `dataset_field_names` attribute on the class.
        The `field_names_in_query` are from the `_fields` query parameter
        in the request to the geosearch.
        Those are checked against `dataset_field_names`.
        """
        return set(self.field_names_in_query or []) & set(self.dataset_field_names or [])

    @classmethod
    def check_scopes(cls, scopes=None):
        """Check who may access this datasource. Access is always allowed if:
            1 no scopes on the datasource
            2 only OPENBAAR on the datasource
        therefore we always add OPENBAAR to the set of user scopes

        Parameters
        ----------

        scopes : str
            The set of scopes assigned to the user
        """
        if scopes is None:
            scopes = {"OPENBAAR"}
        else:
            scopes = set(scopes) | {"OPENBAAR"}

        return cls.metadata.get("scopes", set()).issubset(scopes)

    def filter_dataset(self, dataset_table):
        """
        Filters down the dataset to be just the given dataset
        Expected parameter is dataset name that correlates to the key
        in the dataset table mapping
        """
        for dataset_name, datasets in self.meta["datasets"].items():
            for dataset_ident, table in datasets.items():
                if dataset_ident == dataset_table:
                    self.meta["datasets"] = {dataset_name: {dataset_ident: table}}
                    return True

        self.meta["datasets"] = None
        return False

    def execute_queries(self, datasets=None):
        """Execute queries on all datasets in the datasource.

        Datasets are optionally filtered by `datasets`. Filtering can be
        done with "<dataset/table>" or by "<dataset>". In the latter case
        all tables under that dataset will be queried.

        For example datasets=["bag"] will query all tables under the root "bag"
        in the self.metadata["datasets"] dict.
        """
        datasets = datasets or []
        if "fields" in self.meta:
            self.fields = ",".join(self.meta["fields"])

        features = []
        with self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for dataset in self.meta["datasets"]:
                for dataset_indent, table in self.meta["datasets"][dataset].items():
                    dataset_key = f"{dataset}/{dataset_indent}"
                    if len(datasets) and not any(
                        [
                            dataset in datasets,
                            dataset_key in datasets,
                        ]
                    ):
                        # Actively filter datasets
                        continue

                    if self.meta["operator"] == "contains":
                        rows = self.execute_polygon_query(cur, table, self.temporal_bounds)
                    else:
                        rows = self.execute_point_query(cur, table, self.temporal_bounds)

                    if not len(rows):
                        _logger.debug("no results for table: %s", table)
                        continue

                    for row in rows:
                        features.append(
                            {
                                "properties": {
                                    **{
                                        prop: row[prop]
                                        for prop in self.default_properties
                                        if prop in row
                                    },
                                    **{
                                        toCamelCase(prop): row[prop]
                                        for prop in tuple(self.extra_field_names)
                                        if prop in row
                                    },
                                }
                            }
                        )
        return features

    def get_variable_sql(self, table: str) -> Dict[str, sql.Identifier]:
        """Get the variable sql parts for this
        Datasource as psycopg2 Identifiers and SQL"""

        field_names = self.fields.split(",") + list(self.extra_field_names)

        return dict(
            fields=sql.SQL(", ").join(
                map(sql.SQL, field_names)
            ),  # Properly escape SQL in self.fields
            table_name=sql.Identifier(table.split(".")[1]),
            schema=sql.Identifier(table.split(".")[0]),
            geo_field=sql.Identifier(self.meta["geofield"]),
            extra_where=sql.SQL(self.extra_where),
            limit=sql.SQL("LIMIT {}").format(
                self.limit and sql.Placeholder("limit") or sql.SQL("ALL")
            ),
        )

    def get_db_crs(self) -> sql.Literal:
        if self.crs is None:
            return sql.Literal(28992)
        return sql.Literal(int(self.crs.split(":")[-1]))

    # Point query
    def execute_point_query(self, cur, table, temporal_bounds=None):
        tmp_bounds = sql.SQL("")
        if temporal_bounds is not None:
            start, end = temporal_bounds
            tmp_bounds = sql.SQL(
                " AND ({start} < now() or {start} IS NULL)\
                     AND ({end} > now() OR {end} IS NULL)"
            ).format(start=sql.Identifier(start), end=sql.Identifier(end))

        coordinate_stmt = sql.SQL("ST_GeomFromText('POINT({x} {y})', {crs})")
        if not self.use_rd:
            # In this case, coordinates are latlng and projected to rijksdriehoek
            coordinate_stmt = sql.SQL(
                "ST_Transform(ST_GeomFromText('POINT({y} {x})', 4326), {crs})"
            )
        stmt = sql.SQL(
            """
            SELECT {fields},
                ST_Distance({geo_field},
                {coordinate_stmt}) AS distance
            FROM {schema}.{table_name}
            WHERE ST_DWithin({geo_field}, {coordinate_stmt}, {radius})\
                 {extra_where} {temp_predicate} ORDER BY distance {limit}
        """
        ).format(
            radius=sql.Placeholder("radius"),
            temp_predicate=tmp_bounds,
            coordinate_stmt=coordinate_stmt.format(
                x=sql.Placeholder("x"), y=sql.Placeholder("y"), crs=self.get_db_crs()
            ),
            **self.get_variable_sql(table),
        )
        cur.execute(stmt, {"x": self.x, "y": self.y, "radius": self.radius, "limit": self.limit})
        return cur.fetchall()

    def execute_polygon_query(self, cur, table, temporal_bounds=None):
        tmp_bounds = sql.SQL("")
        if temporal_bounds is not None:
            start, end = temporal_bounds
            tmp_bounds = sql.SQL(
                " AND ({start} < now() or {start} IS NULL)\
                     AND ({end} > now() OR {end} IS NULL)"
            ).format(start=sql.Identifier(start), end=sql.Identifier(end))

        coordinate_stmt = sql.SQL("ST_GeomFromText('POINT({x} {y})', {crs})")
        if not self.use_rd:
            coordinate_stmt = sql.SQL(
                "ST_Transform(ST_GeomFromText('POINT({y} {x})', 4326), {crs})"
            )

        stmt = sql.SQL(
            """
            SELECT {fields},\
                 ST_Distance(ST_Centroid({geo_field}), {coordinate_stmt}) AS distance
            FROM {schema}.{table_name}
            WHERE {geo_field} && {coordinate_stmt}
                AND ST_Contains({geo_field}, {coordinate_stmt})\
                     {extra_where} {temp_predicate} ORDER BY distance
        """
        ).format(
            temp_predicate=tmp_bounds,
            coordinate_stmt=coordinate_stmt.format(
                x=sql.Placeholder("x"), y=sql.Placeholder("y"), crs=self.get_db_crs()
            ),
            **self.get_variable_sql(table),
        )
        cur.execute(stmt, {"x": self.x, "y": self.y})
        return cur.fetchall()

    def query(self, x, y, rd=True, radius=None, limit=None, field_names_in_query=None):
        """Query all datasets in this datasource"""
        self.use_rd = rd
        self.x = x
        self.y = y

        if radius:
            self.radius = radius

        if limit:
            self.limit = limit

        if field_names_in_query:
            self.field_names_in_query = field_names_in_query

        try:
            return {"type": "FeatureCollection", "features": self.execute_queries()}
        except DataSourceException as err:
            return {
                "type": "Error",
                "message": "Error executing query: %s" % err.message,
            }
        except psycopg2.ProgrammingError as err:
            return {
                "type": "Error",
                "message": "Error in database integrity: %s" % repr(err),
            }
        except TypeError as err:
            return {
                "type": "Error",
                "message": "Error in handling, {}".format(repr(err)),
            }


class ExternalDataSource(DataSourceBase):
    """
    ExternalDataSource specification.
    This data source is meant to be used to fetch data from external APIs.

    Class can be initiated with Meta parameter, containing following:
    - base_url is the url of external APIs
    - datasets is a dictionaty with path specification for given source in format:
    ```
    datasets => dict(
        test => dict(
            data => /test/data/
        )
    )
    ```
    - field_mapping is optional key transformation dictionary,
      needed to transform remote response item into geosearch response.

    Request will be performed to: {base_url}/{datasets.keys()}/{datasets[key].keys()}
    Example:
    meta: dict(
        base_url='https://acc.api.data.amsterdam.nl/',
        datasets=dict(
            parkeervakken=dict(
                parkeervakken='parkeervakken/geosearch/'
            )
        )
    )
    Request will be performed on:
     https://acc.api.data.amsterdam.nl/parkeervakken/geosearch/
    """

    dsn_name = None
    radius = None

    def __init__(self, *args, **kwargs):
        if "meta" in kwargs:
            self.meta = kwargs.pop("meta")
        else:
            self.meta = self.metadata.copy()

    def execute_queries(self, datasets=None):
        """
        Execute queries on given datasets.

        :param datasets: list of datasets to filter, optional.
        """
        datasets = datasets or []
        features = []
        request_params = dict(x=self.x, y=self.y)
        if self.limit:
            request_params["limit"] = self.limit
        if self.radius:
            request_params["radius"] = self.radius
        for dataset in self.meta["datasets"]:
            for dataset_indent, subset_url in self.meta["datasets"][dataset].items():
                if len(datasets) and not (dataset in datasets or dataset_indent in datasets):
                    continue

                features += self.fetch_data(
                    dataset_name=f"{dataset}/{dataset_indent}",
                    subset_url=subset_url,
                    request_params=request_params,
                )
        return features

    def fetch_data(self, dataset_name: str, subset_url: str, request_params: dict = None):
        """
        Fetch data from self.meta["base_url"] + subset url and format it
        before returning.
        Wraps requests.RequestException and retuns empty list if it's raisen.

        :param subset_url: relative to self.meta["base_url"] path
        :type subset_url: str
        :param request_params: dictionary with filter arguments or None

        :returns: list of items formatted with self.format_result.
        """
        search_url = urllib.parse.urljoin(self.meta["base_url"], subset_url)
        try:
            result = requests.get(search_url, params=request_params, timeout=1)
        except requests.exceptions.RequestException as e:
            _logger.warning(f"Failed to fetch data from {search_url}. Error '{e}'.")
            return []

        return self.format_result(dataset_name=dataset_name, result=result.json())

    def format_result(self, dataset_name: str, result: list):
        """
        Format result in order to make it look like geosearch native result.

        :param dataset_name: Dataset name to be set as `type` for each item in result
        :param result: response from remote API.

        :returns: list of resulting items formatted according to `field_mapping` spec.
        """
        end_result = []
        for item in result:
            item["type"] = dataset_name
            if self.meta.get("field_mapping") is not None:
                for key, value_template in self.meta["field_mapping"].items():
                    try:
                        item[key] = value_template(self.meta["base_url"], item)
                    except Exception as e:
                        _logger.error(
                            f"Incorrect format template: {key} in {dataset_name}. Error: {e}."  # noqa: E501
                        )
            end_result.append(dict(properties=item))
        return end_result
