import atexit
import logging

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor

import settings

MIN_CONNECTION = 1
MAX_CONNECTION = 2


class DataSourceBase(object):
    """
    Base class for querying geo spatial datasets
    """
    db = None
    dsn = None
    dataset = None
    default_properties = ('id', 'display', 'type', 'uri')
    point_distance = 5
    meta = {}

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Creating DataSource: %s' % self.dataset)

        if not self.dsn:
            raise ValueError('dsn needs to be defined')

        self.pool = SimpleConnectionPool(MIN_CONNECTION, MAX_CONNECTION, self.dsn)
        atexit.register(self._atexit_close_pool)

    def _atexit_close_pool(self):
        if self.pool:
            if not self.pool.closed:
                self.logger.debug('Closing all connections of the connection pool')
                self.pool.closeall()

    def get_cursor(self):
        conn = self.pool.getconn()
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def execute_queries(self, x, y, rd=True):
        cur = self.get_cursor()
        srid = 28992 if rd else 4326
        results, features = [], []

        for table in self.meta['tables']:
            if self.meta['operator'] == 'contains':
                rows = self.execute_polygon_query(cur, table, x, y, srid)
            else:
                rows = self.execute_point_query(cur, table, x, y, srid)

            if not len(rows):
                self.logger.debug(table, 'no results')
                continue

            for row in rows:
                features.append({
                    'properties': dict([(prop, row[prop]) for prop in self.default_properties if prop in row])
                })

        return features

    def execute_point_query(self, cur, table, x, y, srid):
        sql = """
SELECT *
FROM {}
WHERE ST_DWithin({}, ST_GeomFromText(\'POINT(%s %s)\', %s), %d)
""".format(
            table, self.meta['geofield']
        )
        cur.execute(sql, (x, y, srid, self.point_distance)*2)

        return cur.fetchall()

    def execute_polygon_query(self, cur, table, x, y, srid):
        sql = """
SELECT *
FROM {}
WHERE {} && ST_GeomFromText(\'POINT(%s %s)\', %s) AND ST_Contains({}, ST_GeomFromText(\'POINT(%s %s)\', %s))
""".format(
            table, self.meta['geofield'], self.meta['geofield']
        )
        cur.execute(sql, (x, y, srid)*2)

        return cur.fetchall()


class AtlasDataSource(DataSourceBase):
    dsn = settings.DSN_ATLAS
    meta = {
        'tables': [
            'public.geo_bag_bouwblok_mat',
            'public.geo_bag_buurt_mat',
            'public.geo_bag_buurtcombinatie_mat',
            'public.geo_bag_gebiedsgerichtwerken_mat',
            'public.geo_bag_grootstedelijkgebied_mat',
            'public.geo_bag_ligplaats_mat',
            'public.geo_bag_openbareruimte_mat',
            'public.geo_bag_pand_mat',
            'public.geo_bag_stadsdeel_mat',
            'public.geo_bag_standplaats_mat',
            'public.geo_bag_unesco_mat',
            'public.geo_bag_verblijfsobject_mat',
            'public.geo_lki_gemeente_mat',
            'public.geo_lki_kadastraalobject_mat',
            'public.geo_lki_kadastralegemeente_mat',
            'public.geo_lki_sectie_mat',
            'public.geo_wkpb_mat',
        ],
        'geofield': 'geometrie',
        'operator': 'contains',
    }

    def query(self, x, y, rd=False):
        return self.execute_queries(x, y, rd)
