import logging

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import OperationalError, ProgrammingError, connect


class DataSourceException(Exception):
    pass


class DataSourceBase(object):
    """
    Base class for querying geo spatial datasets
    """
    db = None
    dsn = None
    dataset = None
    default_properties = ('id', 'display', 'type', 'uri',  'opr_type')
    radius = 30
    meta = {}
    use_rd = True
    x = None
    y = None

    def __init__(self, dsn=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Creating DataSource: %s' % self.dataset)

        if not dsn:
            raise ValueError('dsn needs to be defined')

        self.dsn = dsn

    def get_cursor(self, conn):
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def execute_queries(self):
        try:
            conn = connect(self.dsn)
        except OperationalError as err:
            self.logger.error('Error creating connection: %s' % err)
            raise DataSourceException('error connecting to datasource')
            return

        features = []
        with self.get_cursor(conn) as cur:
            for dataset in self.meta['datasets']:
                for dataset_ident, table in self.meta['datasets'][dataset].items():
                    if self.meta['operator'] == 'contains':
                        rows = self.execute_polygon_query(cur, table)
                    else:
                        rows = self.execute_point_query(cur, table)

                    if not len(rows):
                        self.logger.debug(table, 'no results')
                        continue

                    for row in rows:
                        features.append({
                            'properties': dict([
                                (prop, row[prop])
                                for prop in self.default_properties if prop in row])
                        })
        # Closing the connection to the db
        conn.close()

        return features

    def execute_point_query(self, cur, table):
        if not self.use_rd:
            sql = """
SELECT *
FROM {}
WHERE ST_DWithin({}, ST_Transform(ST_GeomFromText(\'POINT(%s %s)\', 4326), 28992), %s)
            """.format(
                table, self.meta['geofield']
            )
            cur.execute(sql, (self.y, self.x, self.radius))
        else:
            sql = """
SELECT *
FROM {}
WHERE ST_DWithin({}, ST_GeomFromText(\'POINT(%s %s)\', 28992), %s)
            """.format(
                table, self.meta['geofield']
            )
            cur.execute(sql, (self.x, self.y, self.radius))

        return cur.fetchall()

    def execute_polygon_query(self, cur, table):
        if not self.use_rd:
            sql = """
SELECT *
FROM {}
WHERE {} && ST_Transform(ST_GeomFromText(\'POINT(%s %s)\', 4326), 28992)
AND
ST_Contains({}, ST_Transform(ST_GeomFromText(\'POINT(%s %s)\', 4326), 28992))
            """.format(
                table, self.meta['geofield'], self.meta['geofield']
            )
            cur.execute(sql, (self.y, self.x)*2)
        else:
            sql = """
SELECT *
FROM {}
WHERE {} && ST_GeomFromText(\'POINT(%s %s)\', 28992)
AND
ST_Contains({}, ST_GeomFromText(\'POINT(%s %s)\', 28992))
            """.format(
                table, self.meta['geofield'], self.meta['geofield']
            )
            cur.execute(sql, (self.x, self.y)*2)

        return cur.fetchall()


class AtlasDataSource(DataSourceBase):
    meta = {
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

    def query(self, x, y, rd=True):
        self.use_rd = rd
        self.x = x
        self.y = y

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
        except ProgrammingError as err:
            return {
                'type': 'Error',
                'message': 'Error in database integrity: %s' % repr(err)
            }


class NapMeetboutenDataSource(DataSourceBase):
    meta = {
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

    def query(self, x, y, radius=None, rd=True):
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
        except ProgrammingError as err:
            return {
                'type': 'Error',
                'message': 'Error in database integrity: %s' % repr(err)
            }
