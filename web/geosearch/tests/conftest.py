import pytest
from datapunt_geosearch import config
from datapunt_geosearch.db import dbconnection


@pytest.fixture(scope="session")
def dataservices_db():
    dataservices_db_connection = dbconnection(config.DSN_DATASERVICES_DATASETS)
    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
            BEGIN;
            CREATE TABLE IF NOT EXISTS "datasets_dataset" (
              "id" serial NOT NULL PRIMARY KEY,
              "name" varchar(50) NOT NULL UNIQUE,
              "ordering" integer NOT NULL,
              "enable_api" boolean NOT NULL,
              "schema_data" jsonb NOT NULL,
              "auth" varchar(150) NULL
            );
            CREATE TABLE IF NOT EXISTS "datasets_datasettable" (
              "id" serial NOT NULL PRIMARY KEY,
              "name" varchar(100) NOT NULL,
              "enable_geosearch" boolean NOT NULL,
              "db_table" varchar(100) NOT NULL UNIQUE,
              "auth" varchar(150) NULL,
              "display_field" varchar(50) NULL,
              "geometry_field" varchar(50) NULL,
              "geometry_field_type" varchar(50) NULL,
              "dataset_id" integer NOT NULL
            );

            INSERT INTO "datasets_dataset" (id, name, ordering, enable_api, schema_data) VALUES (
              1,
              'fake',
              1,
              True,
              '9'
            );
            INSERT INTO "datasets_datasettable" (
              id,
              name,
              enable_geosearch,
              db_table,
              display_field,
              geometry_field,
              geometry_field_type,
              dataset_id
            ) VALUES (1, 'fake_public', True, 'fake_fake', 'name', 'geometry', 'POINT', 1);
            INSERT INTO "datasets_datasettable" (
              id,
              name,
              enable_geosearch,
              db_table,
              display_field,
              geometry_field,
              geometry_field_type,
              dataset_id,
              auth
            ) VALUES (2, 'fake_secret', True, 'fake_secret', 'name', 'geometry', 'POINT', 1, 'FAKE/SECRET');
            COMMIT;
            """)

    yield None

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
        BEGIN;
        DROP TABLE "datasets_datasettable" CASCADE;
        DROP TABLE "datasets_dataset" CASCADE;
        COMMIT;
        """)


@pytest.fixture
def dataservices_fake_data():
    dataservices_db_connection = dbconnection(config.DSN_DATASERVICES_DATASETS)
    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS "fake_fake" (
          "id" serial NOT NULL PRIMARY KEY,
          "name" varchar(100) NOT NULL,
          "geometry" geometry(POINT, 28992));
        CREATE TABLE IF NOT EXISTS "fake_secret" (
          "id" serial NOT NULL PRIMARY KEY,
          "name" varchar(100) NOT NULL,
          "geometry" geometry(POINT, 28992));
        """)

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
        BEGIN;
        INSERT INTO "fake_fake" (id, name, geometry) VALUES (
          1,
          'test',
          ST_GeomFromText('POINT(123282.6 487674.8)', 28992));
        INSERT INTO "fake_secret" (id, name, geometry) VALUES (
          1,
          'secret test',
          ST_GeomFromText('POINT(123282.6 487674.8)', 28992));
        COMMIT;
        """)

    yield None

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
        DROP TABLE fake_fake CASCADE;
        DROP TABLE fake_secret CASCADE;
        """)
