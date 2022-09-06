# Setup of local development

Local development is done using docker. We use snapshots of the online databases for development and testing.
Note that these snapshots are not automatically updated when the schema changes, so it is possible that our
tests are running on older versions of the schemas.

1) Ensure containers are running with `docker-compose up`
2) Download and create the different development and test databases with current data dumps from the objectstore.
This process should not take more than 5 minutes on the average internet connection. There is a convenience script
in the root folder for this step, called `init_dbs.sh`
3) Take the testsuite for a spin `docker-compose exec web pytest -v`

**Note**: There have been some issues with connecting to CloudVPS from local docker-containers. This can be circumvented
by downloading the databases onto your host (`download_dbs.sh` is a script to do this), mounting the downloaded dumps into
the `database` container `/tmp` folder and then running `init_dbs.sh` (from step 2 above).

A `docker-compose.override.yml` as the following would mount the directory from `download_dbs.sh` into the database container:

```
version: "3.0"
services:
  database:
    volumes:
      - "/tmp/downloaded_dbs:/tmp"
```

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
<http://localhost:8000/monumenten/?lat=52.372239620672204&lon=4.900848228657843&radius=25000>

<http://localhost:8000/monumenten/?x=121879&y=487262&radius=25000>

<http://localhost:8000/search/?lat=52.372239620672204&lon=4.900848228657843&radius=25000&item=monument>

<http://localhost:8000/search/?x=121879&y=487262&radius=25000&item=monument>

<http://localhost:8000/biz/?x=121723&y=486199>

