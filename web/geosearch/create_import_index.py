# -*- coding: utf-8 -*-
"""
Geosearch master index

Create a master index that should be usable for all geosearches
With this master index we could do one search and find all items
within a specific radius or that contains some specific point

Current counts for different datasets:

kadastraal_object 582551
pand 183659
beperking 45202
meetbout 12904
monument 9420
bouwblok 8597
openbareruimte 6116
ligplaats 2914
peilmerk 874
bominslag 865
verdachtgebied 489
buurt 481
standplaats 321
grondexploitatie 183
uitgevoerdonderzoek 136
buurtcombinatie 99
biz 49
grootstedelijkgebied 36
tellus 28
gebiedsgerichtwerken 22
gevrijwaardgebied 19
stadsdeel 8
unesco 2

"""
import json
import re
from collections import Counter

from datapunt_geosearch.config import DSN_BAG, DSN_MONUMENTEN, DSN_VARIOUS_SMALL_DATASETS, DSN_MILIEU, DSN_NAP, \
    DSN_GRONDEXPLOITATIE

from datapunt_geosearch.datasource import BagDataSource, dbconnection
from datapunt_geosearch.datasource import BominslagMilieuDataSource
from datapunt_geosearch.datasource import MunitieMilieuDataSource
from datapunt_geosearch.datasource import NapMeetboutenDataSource
# from datapunt_geosearch.datasource import TellusDataSource
from datapunt_geosearch.datasource import MonumentenDataSource
from datapunt_geosearch.datasource import GrondExploitatieDataSource
from datapunt_geosearch.datasource import get_dataset_class, get_all_dataset_names

import psycopg2.extras


sources = {
    "bag": {
        'ds': BagDataSource,
        'config': DSN_BAG
    },
    "monumenten": {
        'ds': MonumentenDataSource,
        'config': DSN_MONUMENTEN
    },
    "bominslagmilieu": {
        'ds': BominslagMilieuDataSource,
        'config': DSN_MILIEU
    },
    "munitiemilieu": {
        'ds': MunitieMilieuDataSource,
        'config': DSN_MILIEU
    },
    "nap": {
        'ds': NapMeetboutenDataSource,
        'config': DSN_NAP
    },
    "grondexploitatie": {
        'ds': GrondExploitatieDataSource,
        'config': DSN_GRONDEXPLOITATIE
    },
    # "tellus": {
    #     'ds': TellusDataSource,
    #     'config': DSN_TELLUS
    # },
}


# Mapping van item naar authorisatie scope
required_scopes = {
    'grondexploitatie': 'GREX/R'
}

# URI can be generated
# type can be generated

master_index_table_name = 'geo_master'


def create_index_table(conn):
    with conn.transaction_cursor() as cur:
        # If something went wrong the previous time
        cur.execute(f'''DROP TABLE IF EXISTS {master_index_table_name}_new''')
        cur.execute(f'''
CREATE TABLE {master_index_table_name}_new (
    dataset char varying(36) NOT NULL,
    id char varying(36) NOT NULL,
    display char varying(128),
    wkb_geometry Geometry(Geometry,28992),
    data JSONB,
    PRIMARY KEY(dataset, id)
)
        ''')
        cur.execute(f'''
CREATE INDEX ON {master_index_table_name}_new USING gist (wkb_geometry)        
        ''')


def rename_index_table(conn):
    with conn.transaction_cursor() as cur:
        cur.execute(f'''
ALTER TABLE IF EXISTS {master_index_table_name} rename to {master_index_table_name}_old
        ''')
        cur.execute(f'''
ALTER TABLE {master_index_table_name}_new rename to {master_index_table_name}       
        ''')
        cur.execute(f'''
DROP TABLE IF EXISTS {master_index_table_name}_old        
        ''')


def get_index_data(sources, conn):
    count = Counter()
    with conn.transaction_cursor() as write_cursor:
        for key, value in sources.items():
            print(f"Process {key}")
            ds = value['ds'](value['config'])
            operator = ds.meta['operator']
            geofield = ds.meta['geofield']
            if 'fields' in ds.meta:
                fields = ','.join(ds.meta['fields'])
                for field in ds.meta['fields']:
                    m = re.match(f'''{geofield} as (.*)$''', field)
                    if m:
                        geofield = m.group(1)
            else:
                fields = '*'
            with ds.dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as read_cur:
                for dataset_name, datasets in ds.meta['datasets'].items():
                    for dataset_ident, table in datasets.items():
                        print(f"Processing dataset: {dataset_ident}")
                        if dataset_ident in required_scopes:
                            scope = "'" + required_scopes[dataset_ident] + "'"
                        else:
                            scope = 'NULL'
                        query = """SELECT {} FROM {}""".format(
                            fields,
                            table)
                        read_cur.execute(query)
                        for record in read_cur:
                            count[dataset_ident] += 1
                            if count[dataset_ident] > 0 and (count[dataset_ident] % 1000) == 0:
                                print(f"Processing item {count[dataset_ident]} in {dataset_ident}")
                            uri = record.pop('uri')  # uri can be recreated
                            if 'id' not in record:
                                m = re.search(r'/([0-9\-a-fA-F]+)/$', uri)
                                id1 = m.group(1)
                            else:
                                id1 = record.pop('id')
                            id1 = str(id1)
                            display = record.pop('display')
                            wkb_geometry = record.pop(geofield)
                            record.pop('type', None)  # type can be recreated on  the fly
                            json_data = None if len(record) == 0 else json.dumps(record, default=str)

                            write_cursor.execute(f'''
INSERT INTO {master_index_table_name}_new(dataset, id, display, wkb_geometry, data) 
VALUES(%s, %s, %s, %s, %s)                            
                            ''', (dataset_ident, id1, display, wkb_geometry, json_data))

    for key, item in sorted(count.items(), key=lambda x: x[1], reverse=True):
        print(key, item)


if __name__ == '__main__':
    # First add all data for all generic datasets to the sources
    dataset_names = get_all_dataset_names(dsn=DSN_VARIOUS_SMALL_DATASETS)
    for dataset_name in dataset_names:
        ds_class = get_dataset_class(dataset_name)
        sources[dataset_name] = {
            'ds': ds_class,
            'config': DSN_VARIOUS_SMALL_DATASETS
        }

    conn = dbconnection(DSN_VARIOUS_SMALL_DATASETS)
    create_index_table(conn)
    get_index_data(sources, conn)
    rename_index_table(conn)
