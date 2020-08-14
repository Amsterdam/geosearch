import time
from jwcrypto.jwt import JWT
import pytest
from datapunt_geosearch import config, authz
from datapunt_geosearch.db import dbconnection


@pytest.fixture(scope="session")
def dataservices_db():
    dataservices_db_connection = dbconnection(config.DSN_DATASERVICES_DATASETS)
    with dataservices_db_connection.cursor() as cursor:
        cursor.execute("""
            BEGIN;
            DROP TABLE IF EXISTS "datasets_dataset" CASCADE;
            CREATE TABLE "datasets_dataset" (
              "id" serial NOT NULL PRIMARY KEY,
              "name" varchar(50) NOT NULL UNIQUE,
              "ordering" integer NOT NULL,
              "enable_api" boolean NOT NULL,
              "schema_data" jsonb NOT NULL,
              "auth" varchar(150) NULL
            );
            DROP TABLE IF EXISTS "datasets_datasettable" CASCADE;
            CREATE TABLE "datasets_datasettable" (
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


@pytest.fixture
def create_authz_token(request):
    def _create_authz_token(self, subject, scopes):
        jwks = authz.get_keyset(jwks=config.JWKS)
        assert len(jwks) > 0

        key = next(iter(jwks['keys']))
        now = int(time.time())

        header = {
            'alg': 'ES256',  # algorithm of the test key
            'kid': key.key_id
        }

        token = JWT(
            header=header,
            claims={
                'iat': now,
                'exp': now + 600,
                'scopes': scopes,
                'subject': subject
            })
        token.make_signed_token(key)
        return 'bearer ' + token.serialize()
    request.cls.create_authz_token = _create_authz_token
