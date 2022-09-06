import logging
import urllib.parse
from typing import Dict

import psycopg2.extras
import requests
from psycopg2 import sql

from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

from .config import DATAPUNT_API_URL

_logger = logging.getLogger(__name__)


class DataSourceBase(object):
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
    # Instance specific data
    meta = None
    use_rd = True
    x = None
    y = None
    fields = "*"
    extra_where = ""
    temporal_bounds = None

    def __init__(self, dsn=None, connection=None):
        _logger.debug("Creating DataSource: %s" % self.dataset)

        if not dsn and connection is None:
            raise ValueError("dsn needs to be defined")

        if connection is None:
            try:
                self.dbconn = dbconnection(dsn)
            except psycopg2.Error as e:
                _logger.error("Error creating connection: %s" % e)
                raise DataSourceException("error connecting to datasource") from e
        else:
            self.dbconn = connection

        # why FGS a shallow copy?
        self.meta = self.metadata.copy()

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
                        _logger.debug(table, "no results")
                        continue

                    for row in rows:
                        features.append(
                            {
                                "properties": dict(
                                    [
                                        (prop, row[prop])
                                        for prop in self.default_properties
                                        if prop in row
                                    ]
                                )
                            }
                        )
        return features

    def get_variable_sql(self, table: str) -> Dict[str, sql.Identifier]:
        """Get the variable sql parts for this Datasource as psycopg2 Identifiers and SQL"""
        return dict(
            fields=sql.SQL(", ").join(map(sql.SQL, self.fields.split(","))), # Properly escape SQL in self.fields
            table_name=sql.Identifier(table.split(".")[1]),
            schema=sql.Identifier(table.split(".")[0]),
            geo_field=sql.Identifier(self.meta["geofield"]),
            extra_where=sql.SQL(self.extra_where),
            limit=sql.SQL("LIMIT {}").format(self.limit and sql.Placeholder("limit") or sql.SQL("ALL")),
        )

    # Point query
    def execute_point_query(self, cur, table, temporal_bounds=None):
        tmp_bounds = sql.SQL("")
        if temporal_bounds is not None:
            start, end = temporal_bounds
            tmp_bounds = sql.SQL(
                " AND ({start} < now() or {start} IS NULL) AND ({end} > now() OR {end} IS NULL)"
            ).format(start=sql.Identifier(start), end=sql.Identifier(end))

        coordinate_stmt = sql.SQL("ST_GeomFromText('POINT({x} {y})', 28992)")
        if not self.use_rd:
            # In this case, coordinates are assumed to be latlng and projected to rijksdriehoek
            coordinate_stmt = sql.SQL("ST_Transform(ST_GeomFromText('POINT({y} {x})', 4326), 28992)")
        stmt = sql.SQL("""
            SELECT {fields},
                ST_Distance({geo_field},
                {coordinate_stmt}) AS distance
            FROM {schema}.{table_name}
            WHERE ST_DWithin({geo_field}, {coordinate_stmt}, {radius}) {extra_where} {temp_predicate} ORDER BY distance {limit}
        """).format(
            radius=sql.Placeholder("radius"),
            temp_predicate=tmp_bounds,
            coordinate_stmt=coordinate_stmt.format(
                x=sql.Placeholder("x"),
                y=sql.Placeholder("y"),
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
                " AND ({start} < now() or {start} IS NULL) AND ({end} > now() OR {end} IS NULL)"
            ).format(start=sql.Identifier(start), end=sql.Identifier(end))
    
        coordinate_stmt = sql.SQL("ST_GeomFromText('POINT({x} {y})', 28992)")
        if not self.use_rd:
            coordinate_stmt = sql.SQL("ST_Transform(ST_GeomFromText('POINT({y} {x})', 4326), 28992)")

        stmt = sql.SQL("""
            SELECT {fields}, ST_Distance(ST_Centroid({geo_field}), {coordinate_stmt}) AS distance
            FROM {schema}.{table_name}
            WHERE {geo_field} && {coordinate_stmt} 
                AND ST_Contains({geo_field}, {coordinate_stmt}) {extra_where} {temp_predicate} ORDER BY distance
        """).format(
            temp_predicate=tmp_bounds,
            coordinate_stmt=coordinate_stmt.format(
                x=sql.Placeholder("x"),
                y=sql.Placeholder("y"),
            ),
            **self.get_variable_sql(table),
        )
        cur.execute(stmt, {"x": self.x, "y": self.y})
        return cur.fetchall()

    def query(self, x, y, rd=True, radius=None, limit=None):
        """Query all datasets in this datasource"""
        self.use_rd = rd
        self.x = x
        self.y = y

        if radius:
            self.radius = radius

        if limit:
            self.limit = limit

        try:
            return {"type": "FeatureCollection", "features": self.execute_queries()}
        except DataSourceException as err:
            return {"type": "Error", "message": "Error executing query: %s" % err.message}
        except psycopg2.ProgrammingError as err:
            return {"type": "Error", "message": "Error in database integrity: %s" % repr(err)}
        except TypeError as err:
            return {"type": "Error", "message": "Error in handling, {}".format(repr(err))}


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
    Request will be performed on: https://acc.api.data.amsterdam.nl/parkeervakken/geosearch/
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
        Fetch data from self.meta["base_url"] + subset url and format it before returning.
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
                            f"Incorrect format template: {key} in {dataset_name}. Error: {e}."
                        )
            end_result.append(dict(properties=item))
        return end_result


class BagDataSource(DataSourceBase):
    dsn_name = "DSN_BAG"
    metadata = {
        "geofield": "geometrie",
        "operator": "contains",
        "datasets": {
            "bag": {
                "openbareruimte": "public.geo_bag_openbareruimte_mat",
                "pand": "public.geo_bag_pand_mat",
                "ligplaats": "public.geo_bag_ligplaats_mat",
                "standplaats": "public.geo_bag_standplaats_mat",
            },
            "gebieden": {
                "stadsdeel": "public.geo_bag_stadsdeel_mat",
                "buurt": "public.geo_bag_buurt_mat",
                "buurtcombinatie": "public.geo_bag_buurtcombinatie_mat",
                "bouwblok": "public.geo_bag_bouwblok_mat",
                "grootstedelijkgebied": "public.geo_bag_grootstedelijkgebied_mat",
                "gebiedsgerichtwerken": "public.geo_bag_gebiedsgerichtwerken_mat",
                "unesco": "public.geo_bag_unesco_mat",
            },
            "lki": {
                "kadastraal_object": "public.geo_lki_kadastraalobject_mat",
            },
        },
    }
    default_properties = (
        "id",
        "code",
        "vollcode",
        "display",
        "type",
        "uri",
        "opr_type",
        "distance",
    )

    def filter_dataset(self, dataset_table):
        # Adding custom support voor verblijfsobject as it is not needed
        # in bag but is needed in type specific geosearch
        if dataset_table == "verblijfsobject":
            self.meta["datasets"] = {
                "bag": {"verblijfsobject": "public.geo_bag_verblijfsobject_mat"}
            }
            return True
        else:
            return super(BagDataSource, self).filter_dataset(dataset_table)


class NapMeetboutenDataSource(DataSourceBase):
    dsn_name = "DSN_NAP"
    metadata = {
        "geofield": "geometrie",
        "operator": "within",
        "datasets": {
            "nap": {
                "peilmerk": "public.geo_nap_peilmerk_mat",
            },
            "meetbouten": {
                "meetbout": "public.geo_meetbouten_meetbout_mat",
            },
        },
    }


class MunitieMilieuDataSource(DataSourceBase):
    dsn_name = "DSN_MILIEU"
    metadata = {
        "geofield": "geometrie",
        "operator": "contains",
        "datasets": {
            "munitie": {
                "gevrijwaardgebied": "public.geo_bommenkaart_gevrijwaardgebied_polygon",
                "uitgevoerdonderzoek": "public.geo_bommenkaart_uitgevoerdonderzoek_polygon",
                "verdachtgebied": "public.geo_bommenkaart_verdachtgebied_polygon",
            }
        },
    }
    default_properties = ("id", "display", "type", "uri", "opr_type", "distance")


class BominslagMilieuDataSource(MunitieMilieuDataSource):
    metadata = {
        "geofield": "geometrie",
        "operator": "within",
        "datasets": {"munitie": {"bominslag": "public.geo_bommenkaart_bominslag_point"}},
    }

class MonumentenDataSource(DataSourceBase):
    dsn_name = "DSN_MONUMENTEN"
    metadata = {
        "geofield": "monumentcoordinaten",
        "operator": "within",
        "datasets": {"monumenten": {"monument": "public.dataset_monument"}},
        "fields": [
            "display_naam as display",
            "cast('monumenten/monument' as varchar(30)) as type",
            # "'/monument/' || lower(monumenttype) as type",
            f"'{DATAPUNT_API_URL}monumenten/monumenten/' || id || '/'  as uri",
            "monumentcoordinaten as geometrie",
        ],
    }
    default_properties = ("display", "type", "uri", "distance")

    def query(self, x, y, rd=True, radius=None, limit=None, monumenttype=None):
        self.use_rd = rd
        self.x = x
        self.y = y
        self.monumenttype = monumenttype

        if radius:
            self.radius = radius

        if limit:
            self.limit = limit

        if self.monumenttype:
            monumenttype_list = self.monumenttype.split("_")
            monumenttypes = {"pand", "bouwwerk", "parkterrein", "beeldhouwkunst", "bouwblok"}
            if (
                len(monumenttype_list) >= 2
                and (monumenttype_list[0] == "is" or monumenttype_list[0] == "isnot")
                and all(i in monumenttypes for i in monumenttype_list[1:])
            ):
                operator = "in" if monumenttype_list[0] == "is" else "not in"
                condition = "('" + "','".join(monumenttype_list[1:]) + "')"
                self.extra_where = f" and lower(monumenttype) {operator} {condition}"
            else:
                _logger.warning(f"Invalid monumenttype {self.monumenttype}")
        try:
            return {"type": "FeatureCollection", "features": self.execute_queries()}
        except DataSourceException as err:
            return {"type": "Error", "message": "Error executing query: %s" % err.message}
        except psycopg2.ProgrammingError as err:
            return {"type": "Error", "message": "Error in database integrity: %s" % repr(err)}
        except TypeError as err:
            return {"type": "Error", "message": "Error in handling, {}".format(repr(err))}