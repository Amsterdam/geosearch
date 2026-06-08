import datetime
from importlib import reload
from pathlib import Path

import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.management import call_command
from django.db import connection
from django.test import AsyncClient
from rest_framework.test import APIClient
from schematools.types import DatasetSchema, Scope

from geosearch.registry import get_registry

HERE = Path(__file__).parent


# In test files we use a lot of non-existent scopes, so instead of writing scope
# json files we monkeypatch this method.
@pytest.fixture(autouse=True)
def patch_find_scope_by_id(monkeypatch):
    monkeypatch.setattr(DatasetSchema, "_find_scope_by_id", Scope.from_string)


@pytest.fixture(autouse=True)
def reset_registry():
    global registry
    yield
    registry = reload(__import__("geosearch").registry)


@pytest.fixture
def here() -> Path:
    return HERE


@pytest.fixture()
def api_client() -> APIClient:
    api_client = APIClient()
    api_client.default_format = "json"
    return api_client


@pytest.fixture()
def async_api_client() -> AsyncClient:
    async_api_client = AsyncClient()
    async_api_client.default_format = "json"
    return async_api_client


@pytest.fixture()
def dataset(here):
    dataset_path = here / "files/datasets/dataset"
    args = [dataset_path]
    call_command("import_schemas", *args)


@pytest.fixture()
def dataset_geosearch_disabled(here):
    dataset_path = here / "files/datasets/dataset_geosearch_disabled"
    args = [dataset_path]
    call_command("import_schemas", *args)


@pytest.fixture()
def dataset_scope(here):
    dataset_path = here / "files/datasets/dataset_scope"
    args = [dataset_path]
    call_command("import_schemas", *args)


@pytest.fixture()
def dataset_versions(here):
    dataset_path = here / "files/datasets/dataset_versions"
    args = [dataset_path]
    call_command("import_schemas", *args)


@pytest.fixture()
def dataset_search(here):
    dataset_path = here / "files/datasets/dataset_search"
    args = [dataset_path]
    call_command("import_schemas", *args)


@pytest.fixture()
def dataset_registry():
    registry = get_registry()

    _create_tables_if_missing(registry.get_tables_by_path().values())

    yield registry

    _registry = None


def _create_tables_if_missing(dynamic_models):
    """Create the database tables for dynamic models"""
    table_names = connection.introspection.table_names()

    with connection.schema_editor() as schema_editor:
        for model in dynamic_models:
            if model._meta.db_table not in table_names:
                print(f"Creating table {model._meta.db_table}")
                schema_editor.create_model(model)


@pytest.fixture()
def point(dataset_search, dataset_registry):
    model = dataset_registry.get_table_by_path("dataset_search/point")
    model.objects.get_or_create(id=1, naam="Point 1", geometrie=Point(123282, 487674, srid=28992))
    model.objects.get_or_create(id=2, naam="Point 2", geometrie=Point(123287, 487679, srid=28992))


@pytest.fixture()
def polygon(dataset_search, dataset_registry):
    model = dataset_registry.get_table_by_path("dataset_search/polygon")
    return model.objects.get_or_create(
        id=1,
        naam="Polygon 1",
        geometrie=Polygon(
            (
                (123282, 487674),
                (123292, 487674),
                (123292, 487684),
                (123282, 487684),
                (123282, 487674),
            ),
            srid=28992,
        ),
    )


@pytest.fixture()
def multipolygon(dataset_search, dataset_registry):
    model = dataset_registry.get_table_by_path("dataset_search/multipolygon")

    p1 = Polygon(
        ((123282, 487674), (123292, 487674), (123292, 487684), (123282, 487684), (123282, 487674)),
        srid=28992,
    )
    p2 = Polygon(
        ((123262, 487654), (123272, 487654), (123272, 487664), (123262, 487664), (123262, 487654)),
        srid=28992,
    )

    return model.objects.get_or_create(id=1, naam="Multipolygon 1", geometrie=MultiPolygon(p1, p2))


@pytest.fixture()
def temporal(dataset_search, dataset_registry):
    model = dataset_registry.get_table_by_path("dataset_search/temporal")
    model.objects.get_or_create(
        id="1.1",
        identificatie="1",
        volgnummer=1,
        naam="Temporal 1.1",
        begin_geldigheid=datetime.date(2000, 1, 1),
        eind_geldigheid=datetime.date(2009, 12, 31),
        geometrie=Point(123282, 487674, srid=28992),
    )
    model.objects.get_or_create(
        id="1.2",
        identificatie="2",
        volgnummer=2,
        naam="Temporal 1.2",
        begin_geldigheid=datetime.date(2010, 1, 1),
        geometrie=Point(123282, 487674, srid=28992),
    )


@pytest.fixture()
def dataset_search_filled(point, polygon, multipolygon, temporal):
    pass
