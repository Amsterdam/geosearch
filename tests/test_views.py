"""
Tests for the views.
"""

from unittest.mock import patch

import pytest
from django.db import OperationalError

from tests.utils import build_jwt_token, read_stream


def test_pulse(api_client):
    response = api_client.get("/pulse")
    assert response.status_code == 200
    assert response.data == {"status": "OK"}


@pytest.mark.django_db
def test_health_check(api_client):
    response = api_client.get("/health-check")
    assert response.status_code == 200
    assert response.data == {"status": "OK", "database": "OK"}


@pytest.mark.django_db
def test_health_check_raise_operational_error(api_client):
    with patch("geosearch.views.Dataset.objects.afirst") as mock_dataset:
        mock_dataset.side_effect = OperationalError("Connection timed out")

        response = api_client.get("/health-check")
        assert response.status_code == 500
        assert response.json() == {"detail": "Failed to connect to the database"}


def test_expired_token(api_client):
    """
    Test that an expired token returns a 401 response.
    """
    token = build_jwt_token(["FP/MDW"], expiration=-200)
    response = api_client.get(
        "/geosearch/catalogus/",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "expired_token", "message": "Unauthorized. Token expired."}


def test_invalid_token(api_client):
    """
    Test that an invalid token returns a 401 response.
    """
    token = build_jwt_token(["FP/MDW"], aud="invalid-audience", iss="invalid-issuer")
    response = api_client.get(
        "/geosearch/catalogus/",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_token", "message": "Unauthorized. Invalid token."}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus(async_api_client, dataset, dataset_registry):
    """
    Test that the catalogus endpoint returns the expected datasets, without a token.

    We expect dataset/table without a scope and dataset/field_scope with a scope since field
    scopes are not evaluated.
    """
    response = await async_api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {
        "datasets": [
            "dataset/table",
            "dataset/v1/table",
            "dataset/field_scope",
            "dataset/v1/field_scope",
        ]
    }


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus_table_scope(async_api_client, dataset, dataset_registry):
    """
    Test that the catalogus endpoint returns the expected datasets, with a token.

    Since a token is provided we also expect the dataset/table_scope to be returned.
    """
    token = build_jwt_token(["FP/MDW"])
    response = await async_api_client.get(
        "/geosearch/catalogus/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "datasets": [
            "dataset/table",
            "dataset/v1/table",
            "dataset/table_scope",
            "dataset/v1/table_scope",
            "dataset/field_scope",
            "dataset/v1/field_scope",
        ]
    }


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus_geosearch_disabled(
    async_api_client, dataset_geosearch_disabled, dataset_registry
):
    """Test that the catalogus endpoint doesn't return datasets with geosearch disabled."""
    response = await async_api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {"datasets": []}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus_dataset_scopes_without_token(
    async_api_client, dataset_scope, dataset_registry
):
    """
    Test that the catalogus endpoint doesn't return datasets with dataset scopes
    when no token is provided.
    """
    response = await async_api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {"datasets": []}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus_dataset_scopes_with_token(
    async_api_client, dataset_scope, dataset_registry
):
    """
    Test that the catalogus endpoint returns datasets with dataset scopes when a token
    with the right scope is provided.
    """
    token = build_jwt_token(["FP/MDW"])
    response = await async_api_client.get(
        "/geosearch/catalogus/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"datasets": ["dataset_scope/table", "dataset_scope/v1/table"]}


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_catalogus_with_versions(async_api_client, dataset_versions, dataset_registry):
    """
    Test that the catalogus endpoint returns the versioned datasets.
    """
    response = await async_api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {
        "datasets": [
            "dataset_versions/table",
            "dataset_versions/v1/table",
            "dataset_versions/v2/table",
        ]
    }


@pytest.mark.asyncio
async def test_search_without_coordinates(async_api_client):
    """
    Test that the geosearch endpoint returns an error if no coordinates are provided.
    """
    response = await async_api_client.get("/geosearch/")
    assert response.status_code == 400
    assert response.json() == {
        "non_field_errors": [
            "No coordinates provided. Please provide both x/y or lat/lon coordinates.",
        ]
    }


@pytest.mark.django_db()
@pytest.mark.asyncio
async def test_search_without_datasets(async_api_client, dataset_search):
    """
    Test that the geosearch endpoint returns an empty array if no datasets are provided.
    """
    response = await async_api_client.get("/geosearch/?x=1&y=1")
    data = await read_stream(response)

    assert data == {"type": "FeatureCollection", "features": []}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_within_radius(async_api_client, dataset_search, dataset_search_filled):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&x=123282&y=487674&radius=1"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/point"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_within_radius_with_lat_lon(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&lat=52.37602&lon=4.92142&radius=1"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/point"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_within_radius_with_existing_field(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&x=123282&y=487674&radius=1&_fields=naam"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/point"
    assert data["features"][0]["properties"]["naam"] == "Point 1"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_within_radius_with_non_existing_field(
    async_api_client, dataset_search
):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&x=123282&y=487674&radius=1&_fields=nonexistent"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/point"
    # The non-existing field should not be included in the properties
    assert "nonexistent" not in data["features"][0]["properties"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_multiple_tables_within_radius(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search&x=123282&y=487674&radius=1"
    )
    data = await read_stream(response)

    # We expect four valid features to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 4
    assert all(
        t["properties"]["type"]
        in [
            "dataset_search/point",
            "dataset_search/polygon",
            "dataset_search/multipolygon",
            "dataset_search/temporal",
        ]
        for t in data["features"]
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_within_radius_limit(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&x=123282&y=487674&radius=10&limit=1"
    )
    data = await read_stream(response)

    # We expect one of the two valid points to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/point"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_outside_radius(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/point&x=123262&y=487674&radius=10"
    )
    data = await read_stream(response)

    # We expect no valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_polygon_within_radius(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/polygon&x=123287&y=487679&radius=1"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/polygon"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_polygon_outside_radius(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/polygon&x=123262&y=487674&radius=1"
    )
    data = await read_stream(response)

    # We expect no valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_multipolygon_within_radius(async_api_client, dataset_search):
    """
    Prove that a point within the multipolygon returns a result
    """
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/multipolygon&x=123287&y=487679&radius=1"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/multipolygon"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_multipolygon_outside_large_radius(async_api_client, dataset_search):
    """
    Prove that a point outside the multipolygon, but with a large radius returns a result
    """
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/multipolygon&x=123277&y=487669&radius=20"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/multipolygon"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_multipolygon_outside_radius(async_api_client, dataset_search):
    """
    Prove that a point outside the multipolygon and with a small radius doesn't return a result
    """
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/multipolygon&x=123277&y=487669&radius=1"
    )
    data = await read_stream(response)

    # We expect no valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_search_point_temporal(async_api_client, dataset_search):
    response = await async_api_client.get(
        "/geosearch/?datasets=dataset_search/temporal&x=123282&y=487674&radius=1&_fields=volgnummer,naam"
    )
    data = await read_stream(response)

    # We expect one valid record to be returned
    assert response.status_code == 200
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["type"] == "dataset_search/temporal"
    assert data["features"][0]["properties"]["naam"] == "Temporal 1.2"
    assert data["features"][0]["properties"]["volgnummer"] == 2
    # Make sure identificatie is used and not the raw id field
    assert "." not in data["features"][0]["properties"]["id"]
