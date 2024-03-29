# Setup of local development

## API docs

- go to `https://api.data.amsterdam.nl/api/swagger/?url=/geosearch/docs/geosearch.yml`
- put `/geosearch/docs/geosearch.yml` into the search bar

### Notes

- there is currently no guarantee that these docs are 100% up to date
- the possible datasets/tables that canbe used for filtering can be retrieved from `/catalogus/`
- behavior of filtering on datasets is non-deterministic and opaque because 1) it is not described and 2) if there is a name collision, results may disappear

## Bootstrapping

The dependencies are set up using `pip-compile` which is part of the `pip-tools` package.
So, after creating the virtual env, update the requirements files.
First install `pip-tools` with `pip install pip-tools`.

NB. Because of a problem with cython 3, we need an extra PIP_CONSTRAINT. 
Hopefully, this limitation will be removed in the near future. 
So, first try without the constraint. 
If that works, remove this limitation from this readme.

Now update the `requirements.txt` and `requirements_dev.txt` from the `*.in` files.

1) `echo "cython<3" > /tmp/constraint.txt`
2) `cd web`
3) `PIP_CONSTRAINT=/tmp/constraint.txt pip-compile -o requirements_dev.txt requirements_dev.in`
4) `PIP_CONSTRAINT=/tmp/constraint.txt pip-compile -o requirements.txt requirements.in`

## Virtual env setup for local development

NB. See above about the needed PIP_CONSTRAINT.

1) `cd` to the root of the git repo
2) `PIP_CONSTRAINT=/tmp/constraint.txt pip install -r web/requirements_dev.txt`
3) `pre-commit install`

The local geosearch application can be started with `python web/geosearch/wsgi.py` 
(with an active venv).


## Container setup

Local development can be done using docker. 
We use snapshots of the online databases for development and testing.
Note that these snapshots are not automatically updated when the database schema changes, 
so it is possible that our tests are running on older versions of the schemas.

1) Set the `OS_TENANT_ID` and `OS_AUTH_TOKEN` env vars so we can connect to the object store. (Can be retrieved from openstack)    

    In case of cloudVPS, `OS_AUTH_TOKEN` can be retrieved from the keystone endpoint of the objectstore using:

    ```bash
        export OS_AUTH_TOKEN=$(./get-os-token.sh)
    ```

    where OS_CREDS points to a json formatted file containing the objectstore credentials. this file has the following format:

    ```json
        {
            "auth": {
                "passwordCredentials": {
                    "username": "",
                    "password": ""
                },
                "tenantName": ""
        }
    }
    ```

2) Start database container:

    `docker-compose up database`

3) Setup the databases for local dev and testing:

    `docker-compose exec database init-dbs.sh`

4) Start the app

    `docker-compose up web`

5) Take the testsuite for a spin:

    `docker-compose exec web pytest -v`

**Note**: There have been some issues with connecting to CloudVPS from local docker-containers
over the VET network. This can be circumvented by switching off the VET VPN when running these steps.

## A note on formatting and git blame

black formatting was introduced late in this project by a monster commit.
To avoid git blame getting confused, configure git to ignore that commit:

`$ git config blame.ignoreRevsFile .git-blame-ignore-revs`

# Geospatial queries

Doel is zoeken op coordinaat door de (aangegeven) aanwezige database
views en features teruggeven aan de client in geojson formaat.

## Soorten queries
Er zijn twee soorten postgis queries van toepassing voor de usecase:

* ST_DWithin voor ST_Point velden
* ST_Contains voor ST_Polygon ST_MultiPolygon

We zoeken momenteel nog niet op ST_MultiLineString.

## RD/WGS84
Momenteel is de geometrie opgeslagen in RD srid. We zouden naast deze
kolom een kolom kunnen toevoegen waarin geometrie rsid WGS84 is. Met
deze rsid heeft kunnen we een ST_GeoHash index gebruiken in plaats van
de GEOS filter, wat beter performt.

View & index aanmaken wordt dan zoiets:

`CREATE MATERIALIZED VIEW {}_mat AS SELECT *, ST_Transform(geometrie,
4326) as geometrie_wgs84 FROM {}`

`CREATE INDEX {}_idx ON {}_mat USING GIST(geometrie)`

`GISTCREATE INDEX {}_idx_wgs84 ON {}_mat USING
ST_GeoHash(geometrie_wgs84)`geometrie_wgs84


## Api Endpoints

De volgende endpoints zijn beschikbaar voor geosearch:

- `/nap/` zoek voor NAP data - Locatie en radius verplicht
- `/monumenten/` zoek voor monumenten- Locatie en radius verplicht
- `/munitie/` zoek voor munitie gebieden data - Alleen locatie nodig
- `/bominslag/` zoek voor bominslag data - Locatie en radius verplicht
- `/bag/` Zoek voor BAG, BRK en gebieden data - Alleen locatie nodig
- `/search/` Zoek in alle datasets voor een specifieke item - locatie en item typ nodig. radius is optioneel.

Alle endpoint accepteren of lat/lon (voor WGS84) of x/y voor RD. Als het gaat om gebied zoeken is een radius niet noodzakelijk. Anders moet ook een zoek radius gegeven worden.

### Voorbeelden Api endpoints
<http://localhost:8022/monumenten/?lat=52.372239620672204&lon=4.900848228657843&radius=25000>

<http://localhost:8022/monumenten/?x=121879&y=487262&radius=25000>

<http://localhost:8022/search/?lat=52.372239620672204&lon=4.900848228657843&radius=25000&item=monument>

<http://localhost:8022/search/?x=121879&y=487262&radius=25000&item=monument>

<http://localhost:8022/biz/?x=121723&y=486199>
