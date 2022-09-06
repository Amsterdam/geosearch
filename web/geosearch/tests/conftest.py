import os
import time
from contextlib import contextmanager

import pytest
from jwcrypto.jwt import JWT

from datapunt_geosearch import authz, create_app
from datapunt_geosearch.db import dbconnection

FAKE_SCHEMA = """
{
  "type": "dataset",
  "id": "fake",
  "title": "Fake",
  "status": "beschikbaar",
  "version": "0.0.1",
  "crs": "EPSG:28992",
  "authorizationGrantor": "n.v.t.",
  "owner": "Gemeente Amsterdam",
  "creator": "bronhouder onbekend",
  "publisher": "Datateam Beheer en Openbare Ruimte",
  "tables": [
    {
      "id": "fake_public",
      "type": "table",
      "auth": "OPENBAAR",
      "version": "1.0.0",
      "temporal": {
        "identifier": "volgnummer",
        "dimensions": {
          "geldigOp": [
            "beginGeldigheid",
            "eindGeldigheid"
          ]
        }
      },
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": false,
        "required": [
          "schema",
          "id"
        ],
        "display": "id",
        "properties": {
          "schema": {
            "$ref": "https://schemas.data.amsterdam.nl/schema@v1.1.1#/definitions/schema"
          },
          "id": {
            "type": "integer"
          },
          "name": {
            "type": "string"
          },
          "beginGeldigheid": {
            "type": "string",
            "format": "date-time",
            "description": ""
          },
          "eindGeldigheid": {
            "type": "string",
            "format": "date-time",
            "description": ""
          },
          "geometry": {
            "$ref": "https://geojson.org/schema/Geometry.json"
          }
        }
      }
    },
    {
      "id": "fake_secret",
      "type": "table",
      "auth": "FAKE/SECRET",
      "version": "1.0.0",
      "temporal": {
        "identifier": "volgnummer",
        "dimensions": {
          "geldigOp": [
            "beginGeldigheid",
            "eindGeldigheid"
          ]
        }
      },
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": false,
        "required": [
          "schema",
          "id"
        ],
        "display": "id",
        "properties": {
          "schema": {
            "$ref": "https://schemas.data.amsterdam.nl/schema@v1.1.1#/definitions/schema"
          },
          "id": {
            "type": "integer"
          },
          "name": {
            "type": "string"
          },
          "beginGeldigheid": {
            "type": "string",
            "format": "date-time",
            "description": ""
          },
          "eindGeldigheid": {
            "type": "string",
            "format": "date-time",
            "description": ""
          },
          "geometry": {
            "$ref": "https://geojson.org/schema/Geometry.json"
          }
        }
      }
    }
  ]
}
"""


@pytest.fixture(scope="session", autouse=True)
def flask_test_app():
  """Wraps the entire test session in an app context.
  `autouse` ensures that this fixture gets executed before other fixtures
  in the same scope.
  """
  app = create_app(os.getenv("TEST_SETTINGS_MODULE", "datapunt_geosearch.config"))
  app.testing = True
  ctx = app.app_context()
  ctx.push()
  yield app
  ctx.pop()

@pytest.fixture(scope="class")
def test_client(request, flask_test_app):
  """A client factory wrapped in an Application context"""
  if request.cls is not None:
    request.cls.client = flask_test_app.test_client
  else:
    return flask_test_app.test_client

@pytest.fixture(scope="session")
def dataservices_db(flask_test_app):
    dataservices_db_connection = dbconnection(flask_test_app.config['DSN_DATASERVICES_DATASETS'])
    with dataservices_db_connection.cursor() as cursor:
        cursor.execute(
            f"""
            BEGIN;
            DROP TABLE IF EXISTS "datasets_dataset" CASCADE;
            CREATE TABLE "datasets_dataset" (
              "id" serial NOT NULL PRIMARY KEY,
              "name" varchar(50) NOT NULL UNIQUE,
              "path" varchar(50) NOT NULL UNIQUE,
              "ordering" integer NOT NULL,
              "enable_api" boolean NOT NULL,
              "schema_data" varchar NULL,
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

            INSERT INTO "datasets_dataset" (id, name, path, ordering, enable_api, schema_data) VALUES (
              1,
              'fake',
              'path/fake',
              1,
              True,
              '{FAKE_SCHEMA}'
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
            """
        )

    yield

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute(
            """
        BEGIN;
        DROP TABLE "datasets_datasettable" CASCADE;
        DROP TABLE "datasets_dataset" CASCADE;
        COMMIT;
        """
        )


@pytest.fixture
def dataservices_fake_data(flask_test_app):
    dataservices_db_connection = dbconnection(flask_test_app.config['DSN_DATASERVICES_DATASETS'])
    with dataservices_db_connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS "fake_fake" (
          "id" serial NOT NULL PRIMARY KEY,
          "name" varchar(100) NOT NULL,
          "begin_geldigheid" timestamp without time zone,
          "eind_geldigheid" timestamp without time zone,
          "geometry" geometry(POINT, 28992));
        CREATE TABLE IF NOT EXISTS "fake_secret" (
          "id" serial NOT NULL PRIMARY KEY,
          "name" varchar(100) NOT NULL,
          "begin_geldigheid" timestamp without time zone,
          "eind_geldigheid" timestamp without time zone,
          "geometry" geometry(POINT, 28992));
        """
        )

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute(
            """
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
        """
        )

    yield

    with dataservices_db_connection.cursor() as cursor:
        cursor.execute(
            """
        DROP TABLE fake_fake CASCADE;
        DROP TABLE fake_secret CASCADE;
        """
        )


@pytest.fixture()
def dataservices_fake_temporal_data_creator(request, flask_test_app):
    """Fixture to create additional temporal records.

    NB. This fixture needs to be used in conjunction with `dataservices_fake_data`
    when a full teardown (DROP tables) is needed.
    """
    dataservices_db_connection = dbconnection(flask_test_app.config['DSN_DATASERVICES_DATASETS'])

    @contextmanager
    def _creator(self, begin_geldigheid, eind_geldigheid):
        id_counter = 10
        with dataservices_db_connection.cursor() as cursor:
            cursor.execute(
                f"""
            BEGIN;
            INSERT INTO "fake_fake" (id, name, begin_geldigheid, eind_geldigheid, geometry) VALUES
                (
                  {id_counter},
                  'test-2',
                  {begin_geldigheid},
                  {eind_geldigheid},
                  ST_GeomFromText('POINT(123282.6 487674.8)', 28992)
                );
            COMMIT;
            """
            )
            id_counter += 1
            yield
            with dataservices_db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    BEGIN;
                    DELETE FROM "fake_fake"
                    WHERE id >= 10;
                    COMMIT;
                """
                )

    request.cls.data_creator = _creator


@pytest.fixture
def create_authz_token(request, flask_test_app):
    def _create_authz_token(self, subject, scopes):
        jwks = authz.get_keyset(jwks=flask_test_app.config['JWKS'])
        assert len(jwks) > 0

        key = next(iter(jwks["keys"]))
        now = int(time.time())

        header = {"alg": "ES256", "kid": key.key_id}  # algorithm of the test key

        token = JWT(
            header=header,
            claims={"iat": now, "exp": now + 600, "scopes": scopes, "subject": subject},
        )
        token.make_signed_token(key)
        return "bearer " + token.serialize()

    request.cls.create_authz_token = _create_authz_token
