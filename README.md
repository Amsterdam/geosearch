# Geospatial queries

Doel is zoeken op coordinaat door de (aangegeven) aanwezige database
views en features teruggeven aan de client in geojson formaat.

Momenteel gebruiken we mapserver's WFS mogelijkheden hiervoor, maar dit
is verre van ideaal. Mapserver geojson laten retourneren met meerdere
lagen per request gaat niet goed. Gevolg is een request per layer doen
vanuit de frontend bij klik op kaart.

Het enige wat mapserver doet in deze is de XML(!) filter vertalen naar
een postgis query, en de resultaten teruggeven aan de client. Iets wat
in dit geval beter via een API kan dmv 1 request: geef me alle features
voor dit coordinaat (optioneel beperkt tot deze layers).

## Taal/framework keuze
Django channels zou interessant kunnen zijn te gebruiken voor de search
queries vanuit de client, naast een "normale" API. Wel overkill voor een
simpele API.

Flask/SQLAlchemy zou wat dit betreft een betere keuze zijn.

Andere keuze zou kunnen zijn een Node/Express applicatie, omdat we niet
echt aan models gebonden zijn en er gewone SQL statements worden
uitgevoerd.

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



