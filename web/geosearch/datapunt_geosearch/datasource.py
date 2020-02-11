import logging
import psycopg2.extras

from .config import DATAPUNT_API_URL
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException
from datapunt_geosearch.registry import registry


_logger = logging.getLogger(__name__)


class DataSourceBase(object):
    """
    Base class for querying geo spatial datasets
    """
    db = None
    dsn = None
    dataset = None
    # opr_type = openbare_ruimte_type. Water, Weg, Terrein...
    default_properties = ('id', 'display', 'type', 'uri', 'opr_type', 'distance')
    radius = 30
    limit = None
    # Generic Meta for all instances of this DataSource
    metadata = {}
    # Instance specific data
    meta = None
    use_rd = True
    x = None
    y = None
    fields = '*'
    extra_where = ''

    def __init__(self, dsn=None, connection=None):
        _logger.debug('Creating DataSource: %s' % self.dataset)

        if not dsn and connection is None:
            raise ValueError('dsn needs to be defined')

        if connection is None:
            try:
                self.dbconn = dbconnection(dsn)
            except psycopg2.Error as e:
                _logger.error('Error creating connection: %s' % e)
                raise DataSourceException('error connecting to datasource') from e
        else:
            self.dbconn = connection

        self.meta = self.metadata.copy()

    def filter_dataset(self, dataset_table):
        """
        Filters down the dataset to be just the given dataset
        Expected parameter is dataset name that correlates to the key
        in the dataset table mapping
        """
        for dataset_name, datasets in self.meta['datasets'].items():
            for dataset_ident, table in datasets.items():
                if dataset_ident == dataset_table:
                    self.meta['datasets'] = {
                        dataset_name: {
                            dataset_ident: table
                        }
                    }
                    return True

        self.meta['datasets'] = None
        return False

    def execute_queries(self, datasets=None):
        datasets = datasets or []
        if 'fields' in self.meta:
            self.fields = ','.join(self.meta['fields'])

        features = []
        with self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for dataset in self.meta['datasets']:
                for dataset_indent, table in self.meta['datasets'][dataset].items():
                    if len(datasets) and not (
                            dataset in datasets or dataset_indent in datasets):
                        # Actively filter datasets
                        continue

                    if self.meta['operator'] == 'contains':
                        rows = self.execute_polygon_query(cur, table)
                    else:
                        rows = self.execute_point_query(cur, table)

                    if not len(rows):
                        _logger.debug(table, 'no results')
                        continue

                    for row in rows:
                        features.append({
                            'properties': dict([(prop, row[prop])
                                                for prop in
                                                self.default_properties if
                                                prop in row])})
        return features

    # Point query
    def execute_point_query(self, cur, table):
        if not self.use_rd:
            sql = """
SELECT {}, ST_Distance({}, ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), 28992)) as distance
FROM {}
WHERE ST_DWithin({}, ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), 28992), %s) {}
ORDER BY distance
            """.format(
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.extra_where
            )
            if self.limit:
                sql += "LIMIT %s"
                cur.execute(sql, (self.y, self.x, self.y, self.x, self.radius, self.limit))
            else:
                cur.execute(sql, (self.y, self.x, self.y, self.x, self.radius))
        else:
            sql = """
SELECT {}, ST_Distance({}, ST_GeomFromText('POINT(%s %s)', 28992)) as distance
FROM {}
WHERE ST_DWithin({}, ST_GeomFromText('POINT(%s %s)', 28992), %s) {}
ORDER BY distance
            """.format(
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.extra_where
            )
            if self.limit:
                sql += "LIMIT %s"
                cur.execute(sql, (self.x, self.y, self.x, self.y, self.radius, self.limit))
            else:
                cur.execute(sql, (self.x, self.y, self.x, self.y, self.radius))
        return cur.fetchall()

    def execute_polygon_query(self, cur, table):
        if not self.use_rd:
            sql = """
SELECT {}, ST_Distance(ST_Centroid({}), ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), 28992)) as distance
FROM {}
WHERE {} && ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), 28992)
AND
ST_Contains({}, ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), 28992)) {}
ORDER BY distance
            """.format(
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.meta['geofield'],
                self.extra_where
            )
            cur.execute(sql, (self.y, self.x) * 3)
        else:
            sql = """
SELECT {}, ST_Distance(ST_Centroid({}), ST_GeomFromText('POINT(%s %s)', 28992)) as distance
FROM {}
WHERE {} && ST_GeomFromText('POINT(%s %s)', 28992)
AND
ST_Contains({}, ST_GeomFromText('POINT(%s %s)', 28992)) {}
ORDER BY distance
            """.format(
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.meta['geofield'],
                self.extra_where
            )
            cur.execute(sql, (self.x, self.y) * 3)

        return cur.fetchall()

    def query(self, x, y, rd=True, radius=None, limit=None):
        self.use_rd = rd
        self.x = x
        self.y = y

        if radius:
            self.radius = radius

        if limit:
            self.limit = limit

        try:
            return {
                'type': 'FeatureCollection',
                'features': self.execute_queries()
            }
        except DataSourceException as err:
            return {
                'type': 'Error',
                'message': 'Error executing query: %s' % err.message
            }
        except psycopg2.ProgrammingError as err:
            return {
                'type': 'Error',
                'message': 'Error in database integrity: %s' % repr(err)
            }
        except TypeError as err:
            return {
                'type': 'Error',
                'message': 'Error in handling, {}'.format(repr(err))
            }


class BagDataSource(DataSourceBase):
    dsn_name = 'DSN_BAG'
    metadata = {
        'geofield': 'geometrie',
        'operator': 'contains',
        'datasets': {
            'bag': {
                'openbareruimte': 'public.geo_bag_openbareruimte_mat',
                'pand': 'public.geo_bag_pand_mat',
                'ligplaats': 'public.geo_bag_ligplaats_mat',
                'standplaats': 'public.geo_bag_standplaats_mat',
            },
            'gebieden': {
                'stadsdeel': 'public.geo_bag_stadsdeel_mat',
                'buurt': 'public.geo_bag_buurt_mat',
                'buurtcombinatie': 'public.geo_bag_buurtcombinatie_mat',
                'bouwblok': 'public.geo_bag_bouwblok_mat',
                'grootstedelijkgebied': 'public.geo_bag_grootstedelijkgebied_mat',
                'gebiedsgerichtwerken': 'public.geo_bag_gebiedsgerichtwerken_mat',
                'unesco': 'public.geo_bag_unesco_mat',
            },
            'lki': {
                'kadastraal_object': 'public.geo_lki_kadastraalobject_mat',
            },
            'wkpb': {
                'beperking': 'public.geo_wkpb_mat',
            },
        },
    }
    default_properties = ('id', 'code', 'vollcode', 'display', 'type', 'uri', 'opr_type', 'distance')

    def filter_dataset(self, dataset_table):
        # Adding custom support voor verblijfsobject as it is not needed
        # in bag but is needed in type specific geosearch
        if dataset_table == 'verblijfsobject':
            self.meta['datasets'] = {'bag': {
                'verblijfsobject': 'public.geo_bag_verblijfsobject_mat'}}
            return True
        else:
            return super(BagDataSource, self).filter_dataset(dataset_table)


class NapMeetboutenDataSource(DataSourceBase):
    dsn_name = 'DSN_NAP'
    metadata = {
        'geofield': 'geometrie',
        'operator': 'within',
        'datasets': {
            'nap': {
                'peilmerk': 'public.geo_nap_peilmerk_mat',
            },
            'meetbouten': {
                'meetbout': 'public.geo_meetbouten_meetbout_mat',
            },
        },
    }


class MunitieMilieuDataSource(DataSourceBase):
    dsn_name = 'DSN_MILIEU'
    metadata = {
        'geofield': 'geometrie',
        'operator': 'contains',
        'datasets': {
            'munitie': {
                'gevrijwaardgebied':
                    'public.geo_bommenkaart_gevrijwaardgebied_polygon',
                'uitgevoerdonderzoek':
                    'public.geo_bommenkaart_uitgevoerdonderzoek_polygon',
                'verdachtgebied':
                    'public.geo_bommenkaart_verdachtgebied_polygon'
            }
        },
    }
    default_properties = ('id', 'display', 'type', 'uri', 'opr_type', 'distance')


class BominslagMilieuDataSource(MunitieMilieuDataSource):
    metadata = {
        'geofield': 'geometrie',
        'operator': 'within',
        'datasets': {
            'munitie': {'bominslag': 'public.geo_bommenkaart_bominslag_point'}
        },
    }


# class TellusDataSource(DataSourceBase):
#     def __init__(self, *args, **kwargs):
#         super(TellusDataSource, self).__init__(*args, **kwargs)
#         self.meta = {
#             'geofield': 'geometrie',
#             'operator': 'within',
#             'datasets': {
#                 'tellus': {
#                     'tellus':
#                         'public.geo_tellus_point'
#                 }
#             },
#         }
#
#     default_properties = ('display', 'standplaats', 'type', 'uri', 'distance')
#
#     def query(self, x, y, rd=True, radius=None, limit=None):
#         self.use_rd = rd
#         self.x = x
#         self.y = y
#
#         if radius:
#             self.radius = radius
#
#         try:
#             return {
#                 'type': 'FeatureCollection',
#                 'features': self.execute_queries()
#             }
#         except DataSourceException as err:
#             return {
#                 'type': 'Error',
#                 'message': 'Error executing query: %s' % err.message
#             }
#         except psycopg2.ProgrammingError as err:
#             return {
#                 'type': 'Error',
#                 'message': 'Error in database integrity: %s' % repr(err)
#             }
#         except TypeError as err:
#             return {
#                 'type': 'Error',
#                 'message': 'Error in handling, {}'.format(repr(err))
#             }


class MonumentenDataSource(DataSourceBase):
    dsn_name = 'DSN_MONUMENTEN'
    metadata = {
        'geofield': 'monumentcoordinaten',
        'operator': 'within',
        'datasets': {
            'monumenten': {
                'monument':
                    'public.dataset_monument'
            }
        },
        'fields': [
            "display_naam as display",
            "cast('monumenten/monument' as varchar(30)) as type",
            # "'/monument/' || lower(monumenttype) as type",
            f"'{DATAPUNT_API_URL}monumenten/monumenten/' || id || '/'  as uri",
            "monumentcoordinaten as geometrie",
        ],
    }
    default_properties = ('display', 'type', 'uri', 'distance')

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
            monumenttype_list = self.monumenttype.split('_')
            monumenttypes = {'pand', 'bouwwerk', 'parkterrein', 'beeldhouwkunst', 'bouwblok'}
            if len(monumenttype_list) >= 2 and (monumenttype_list[0] == 'is' or monumenttype_list[0] == 'isnot') and \
                    all(i in monumenttypes for i in monumenttype_list[1:]):
                operator = 'in' if monumenttype_list[0] == 'is' else 'not in'
                condition = "('" + "','".join(monumenttype_list[1:]) + "')"
                self.extra_where = f' and lower(monumenttype) {operator} {condition}'
            else:
                _logger.warning(f"Invalid monumenttype {self.monumenttype}")
        try:
            return {
                'type': 'FeatureCollection',
                'features': self.execute_queries()
            }
        except DataSourceException as err:
            return {
                'type': 'Error',
                'message': 'Error executing query: %s' % err.message
            }
        except psycopg2.ProgrammingError as err:
            return {
                'type': 'Error',
                'message': 'Error in database integrity: %s' % repr(err)
            }
        except TypeError as err:
            return {
                'type': 'Error',
                'message': 'Error in handling, {}'.format(repr(err))
            }


registry.register_dataset('DSN_BAG', BagDataSource)
registry.register_dataset('DSN_NAP', NapMeetboutenDataSource)
registry.register_dataset('DSN_MUNITIE', MunitieMilieuDataSource)
registry.register_dataset('DSN_MUNITIE', BominslagMilieuDataSource)
registry.register_dataset('DSN_MONUMENTEN', MonumentenDataSource)


def get_dataset_class(ds_name, dsn=None):
    """
    When this method is called the first time the catalog is read and for all
    datasets in the catalog a subclass of DataSource is created and added to the
    _datasets mapping
    :param ds_name: Name of dataset (ie 'biz')
    :param dsn optional datasource name for reading catalog. Required for testing
    :return: subclass of DataSource for this dataset
    """
    return registry.get_by_name(ds_name)


def get_all_dataset_names(dsn=None):
    return registry.get_all_dataset_names()
