from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient
from schematools.types import DatasetSchema, Scope

HERE = Path(__file__).parent


# In test files we use a lot of non-existent scopes, so instead of writing scope
# json files we monkeypatch this method.
@pytest.fixture(autouse=True)
def patch_find_scope_by_id(monkeypatch):
    monkeypatch.setattr(DatasetSchema, "_find_scope_by_id", Scope.from_string)


@pytest.fixture
def here() -> Path:
    return HERE


@pytest.fixture()
def api_client() -> APIClient:
    api_client = APIClient()
    api_client.default_format = "json"  # instead of multipart
    return api_client


@pytest.fixture()
def dataset(here):
    dataset_path = here / "files/datasets/dataset"
    args = [dataset_path]
    call_command("import_schemas", *args, dry_run=False)


@pytest.fixture()
def dataset_geosearch_disabled(here):
    dataset_path = here / "files/datasets/dataset_geosearch_disabled"
    args = [dataset_path]
    call_command("import_schemas", *args, dry_run=False)


@pytest.fixture()
def dataset_scope(here):
    dataset_path = here / "files/datasets/dataset_scope"
    args = [dataset_path]
    call_command("import_schemas", *args, dry_run=False)


@pytest.fixture()
def dataset_versions(here):
    dataset_path = here / "files/datasets/dataset_versions"
    args = [dataset_path]
    call_command("import_schemas", *args, dry_run=False)
