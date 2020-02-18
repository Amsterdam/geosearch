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
              "schema_data" jsonb NOT NULL
            );
            CREATE TABLE IF NOT EXISTS "datasets_datasettable" (
              "id" serial NOT NULL PRIMARY KEY,
              "name" varchar(100) NOT NULL,
              "enable_geosearch" boolean NOT NULL,
              "db_table" varchar(100) NOT NULL UNIQUE,
              "display_field" varchar(50) NULL,
              "geometry_field" varchar(50) NULL,
              "geometry_field_type" varchar(50) NULL,
              "dataset_id" integer NOT NULL
            );
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
        """)

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
        BEGIN;
        INSERT INTO "datasets_dataset" (id, name, ordering, enable_api, schema_data) VALUES (
          1,
          'fake',
          1,
          True,
          '9');
        INSERT INTO "datasets_datasettable" (
          id,
          name,
          enable_geosearch,
          db_table,
          display_field,
          geometry_field,
          geometry_field_type,
          dataset_id
        ) VALUES (1, 'fake', True, 'fake_fake', 'name', 'geometry', 'POINT', 1);
        INSERT INTO "fake_fake" (id, name, geometry) VALUES (
          1,
          'test',
          ST_GeomFromText('POINT(123282.6 487674.8)', 28992));
        COMMIT;
        """)

    yield None

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("DROP TABLE fake_fake CASCADE;")


@pytest.fixture(scope="session")
def vsd_db():
    vsd_db_connection = dbconnection(config.DSN_VARIOUS_SMALL_DATASETS)
    sql = """
    BEGIN;
    CREATE TABLE IF NOT EXISTS "cat_dataset" (
      "id" serial NOT NULL PRIMARY KEY,
      "name" varchar(30) NOT NULL UNIQUE,
      "description" text NULL,
      "database" varchar(128) NULL,
      "schema" varchar(128) NULL,
      "table_name" varchar(128) NOT NULL,
      "ordering" varchar(128) NULL,
      "pk_field" varchar(128) NULL,
      "enable_api" boolean NOT NULL,
      "name_field" varchar(128) NULL,
      "geometry_field" varchar(128) NULL,
      "geometry_type" varchar(32) NOT NULL,
      "enable_geosearch" boolean NOT NULL,
      "enable_maplayer" boolean NOT NULL,
      "map_template" varchar(128) NULL,
      "map_title" varchar(128) NULL,
      "map_abstract" varchar(128) NULL);
    COMMIT;
    """
    with vsd_db_connection.cursor() as cursor:
        cursor.execute(sql)

    yield None

    with vsd_db_connection.cursor() as cursor:
        cursor.execute("DROP TABLE cat_dataset CASCADE")


@pytest.fixture
def vsd_biz_data():
    vsd_db_connection = dbconnection(config.DSN_VARIOUS_SMALL_DATASETS)

    with vsd_db_connection.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS "biz" (
          "id" serial NOT NULL PRIMARY KEY,
          "naam" varchar(100) NOT NULL,
          "geometrie" geometry(POINT, 28992));
        """)
    sql = """
    BEGIN;
    INSERT INTO "cat_dataset" (
      name,
      description,
      table_name,
      pk_field,
      name_field,
      geometry_field,
      geometry_type,
      enable_api,
      enable_geosearch,
      enable_maplayer)
    VALUES (
      'biz',
      'Fake biz data',
      'biz',
      'id',
      'naam',
      'geometrie',
      'POINT',
      True,
      True,
      True);
    INSERT INTO biz (naam, geometrie) VALUES ('Utrechtsestraat', ST_GeomFromText('POINT(121723 486199)', 28992));
    INSERT INTO biz (naam, geometrie) VALUES (
      'Oud West',
      ST_Transform(ST_GeomFromText('POINT(4.87529 52.36287)', 4326), 28992));
    COMMIT;
    """
    with vsd_db_connection.cursor() as cursor:
        cursor.execute(sql)

    yield None

    with vsd_db_connection.cursor() as cursor:
        cursor.execute("""
        BEGIN;
        DELETE FROM cat_dataset WHERE description = 'Fake biz data';
        DROP TABLE biz CASCADE;
        COMMIT;
        """)
