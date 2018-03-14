import contextlib
import functools
import logging
from .config import DATAPUNT_API_URL

import psycopg2.extras

_logger = logging.getLogger(__name__)


@functools.lru_cache()
def dbconnection(dsn):
    """Creates an instance of _DBConnection and remembers the last one made."""
    return _DBConnection(dsn)


class _DBConnection:
    """ Wraps a PostgreSQL database connection that reports crashes and tries
    its best to repair broken connections.

    NOTE: doesn't always work, but the failure scenario is very hard to
      reproduce. Also see https://github.com/psycopg/psycopg2/issues/263
    """

    def __init__(self, *args, **kwargs):
        self.conn_args = args
        self.conn_kwargs = kwargs
        self._conn = None
        self._connect()

    def _connect(self):
        if self._conn is None:
            self._conn = psycopg2.connect(*self.conn_args, **self.conn_kwargs)
            self._conn.autocommit = True

    def _is_usable(self):
        """ Checks whether the connection is usable.

        :returns boolean: True if we can query the database, False otherwise
        """
        try:
            self._conn.cursor().execute("SELECT 1")
        except psycopg2.Error:
            return False
        else:
            return True

    @contextlib.contextmanager
    def _connection(self):
        """ Contextmanager that catches tries to ensure we have a database
        connection. Yields a Connection object.

        If a :class:`psycopg2.DatabaseError` occurs then it will check whether
        the connection is still usable, and if it's not, close and remove it.
        """
        try:
            self._connect()
            yield self._conn
        except psycopg2.Error as e:
            _logger.critical('AUTHZ DatabaseError: {}'.format(e))
            if not self._is_usable():
                with contextlib.suppress(psycopg2.Error):
                    self._conn.close()
                self._conn = None
            raise e

    @contextlib.contextmanager
    def transaction_cursor(self, cursor_factory=None):
        """ Yields a cursor with transaction.
        """
        with self._connection() as transaction:
            with transaction:
                with transaction.cursor(cursor_factory=cursor_factory) as cur:
                    yield cur

    @contextlib.contextmanager
    def cursor(self, cursor_factory=None):
        """ Yields a cursor without transaction.
        """
        with self._connection() as conn:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                yield cur


class DataSourceException(Exception):
    pass


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
    meta = {}
    use_rd = True
    x = None
    y = None
    fields = '*'
    extra_where = ''

    def __init__(self, dsn=None):
        _logger.debug('Creating DataSource: %s' % self.dataset)

        if not dsn:
            raise ValueError('dsn needs to be defined')

        try:
            self.dbconn = dbconnection(dsn)
        except psycopg2.Error as e:
            _logger.error('Error creating connection: %s' % e)
            raise DataSourceException('error connecting to datasource') from e

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

    def execute_queries(self):
        if 'fields' in self.meta:
            self.fields = ','.join(self.meta['fields'])

        features = []
        with self.dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for dataset in self.meta['datasets']:
                for _, table in self.meta['datasets'][dataset].items():
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
                self.fields,self.meta['geofield'], table, self.meta['geofield'], self.extra_where
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
AND ST_IsValid({})
ORDER BY distance
            """.format(
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.meta['geofield'], self.extra_where, self.meta['geofield']
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
                self.fields, self.meta['geofield'], table, self.meta['geofield'], self.meta['geofield'], self.extra_where
            )
            cur.execute(sql, (self.x, self.y) * 3)

        return cur.fetchall()


class BagDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(BagDataSource, self).__init__(*args, **kwargs)
        self.meta = {
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

    def filter_dataset(self, dataset_table):
        # Adding custom support voor verblijfsobject as it is not needed
        # in bag but is needed in type specific geosearch
        if dataset_table == 'verblijfsobject':
            self.meta['datasets'] = {'bag': {
                'verblijfsobject': 'public.geo_bag_verblijfsobject_mat'}}
            return True
        else:
            return super(BagDataSource, self).filter_dataset(dataset_table)

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


class NapMeetboutenDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(NapMeetboutenDataSource, self).__init__(*args, **kwargs)
        self.meta = {
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


class MunitieMilieuDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(MunitieMilieuDataSource, self).__init__(*args, **kwargs)
        self.meta = {
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


class BominslagMilieuDataSource(MunitieMilieuDataSource):

    def __init__(self, *args, **kwargs):
        super(BominslagMilieuDataSource, self).__init__(*args, **kwargs)
        self.meta['datasets'] = {
            'munitie': {'bominslag': 'public.geo_bommenkaart_bominslag_point'}
        }
        self.meta['operator'] = 'within'


class TellusDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(TellusDataSource, self).__init__(*args, **kwargs)
        self.meta = {
            'geofield': 'geometrie',
            'operator': 'within',
            'datasets': {
                'tellus': {
                    'tellus':
                        'public.geo_tellus_point'
                }
            },
        }

    default_properties = ('display', 'standplaats', 'type', 'uri', 'distance')

    def query(self, x, y, rd=True, radius=None, limit=None):
        self.use_rd = rd
        self.x = x
        self.y = y

        if radius:
            self.radius = radius

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


class MonumentenDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(MonumentenDataSource, self).__init__(*args, **kwargs)
        self.meta = {
            'geofield': 'monumentcoordinaten',
            'operator': 'within',
            'datasets': {
                'monumenten': {
                    'monument':
                        'public.dataset_monument'
                }
            },
            'fields' : [
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

class GrondExploitatieDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(GrondExploitatieDataSource, self).__init__(*args, **kwargs)
        self.meta = {
            'geofield': 'wkb_geometry',
            'operator': 'contains',
            'datasets': {
                'grondexploitatie': {
                    'grondexploitatie':
                        'public.grex_grenzen_ogagis_2016'
                }
            },
            'fields' : [
                "plannaam as display",
                "cast('grex/grondexploitatie' as varchar(30)) as type",
                f"'{DATAPUNT_API_URL}grondexploitatie/project/' || plannr || '/'  as uri",
                "wkb_geometry as geometrie",
            ],
        }

    default_properties = ('display', 'type', 'uri', 'distance')

    def query(self, x, y, rd=True, radius=None, limit=None):
        self.use_rd = rd
        self.x = x
        self.y = y

        if radius:
            self.radius = radius

        if limit:
            self.limit = limit

        self.extra_where = " and planstatus in ('A', 'T')"
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

class BIZDataSource(DataSourceBase):
    def __init__(self, *args, **kwargs):
        super(BIZDataSource, self).__init__(*args, **kwargs)
        self.meta = {
            'geofield': 'wkb_geometry',
            'operator': 'contains',
            'datasets': {
                '': {
                    'various_small_datasets':
                        'public.biz_data'
                }
            },
            'fields' : [
                "naam as display",
                "cast('vsd/biz' as varchar(30)) as type",
                f"'{DATAPUNT_API_URL}vsd/biz/' || biz_id || '/'  as uri",
                "wkb_geometry as geometrie",
                "biz_id",
                "biz_type",
                "heffingsgrondslag",
                "website",
                "heffing",
                "bijdrageplichtigen",
                "verordening",
            ],
        }

    default_properties = ('display', 'type', 'uri', 'biz_id', 'biz_type', 'heffingsgrondslag', 'website', 'heffing', 'bijdrageplichtigen', 'verordening', 'distance')

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