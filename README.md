# setup


Update different project databases with current data:
bag_backend and meetbouten for now

    docker-compose up -d
    docker-compose exec bag_db update-db.sh  bag <your_username>
    docker-compose exec nap_db update-db.sh nap <your_username>
    docker-compose exec milieuthemas_db update-db.sh milieuthemas <your_username>
    docker-compose exec monumenten_db update-db.sh monumenten <your_username>
    docker-compose exec tellus_db update-db.sh tellus  <your_username>

    pip install -r requirements.txt

test postgres spatial queries:

    cd web/geosearch
	python test_dataset.py



# Geospatial queries

Doel is zoeken op coordinaat door de (aangegeven) aanwezige database
views en features teruggeven aan de client in geojson formaat.

## Taal/framework keuze

Flask

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

- `/nap/` zoek voor NAP data - Locatie en radius verplict
- `/monumenten/` zoek voor monumenten- Locatie en radius verplicht
- `/munitie/` zoek voor munitie gebieden data - Alleen locatie nodig
- `/bominslag/` zoek voor bominslag data - Locatie en radius verplict
- `/bag/` Zoek voor BAG, BRK en gebieden data - Alleen locatie nodig
- `/search/` Zoek in alle datasets voor een specifieke item - locatie en item typ nodig. radius is optioneel.

Alle endpoint accepteren of lat/lon (voor WGS84) of x/y voor RD. Als het gaat om gebied zoeken is een radius niet noodzakelijk. Anders moet ook een zoek radius gegeven worden.

### Voorbeelden Api endpoints
<http://localhost:8000/monumenten/?lat=52.372239620672204&lon=4.900848228657843&radius=25000>

<http://localhost:8000/monumenten/?x=121879&y=487262&radius=25000>

<http://localhost:8000/search/?lat=52.372239620672204&lon=4.900848228657843&radius=25000&item=monument>

<http://localhost:8000/search/?x=121879&y=487262&radius=25000&item=monument>
