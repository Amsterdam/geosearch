"""
Tests for the views.
"""

from unittest.mock import patch

import pytest
from django.db import OperationalError

from tests.utils import build_jwt_token


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
def test_catalogus(api_client, dataset):
    """
    Test that the catalogus endpoint returns the expected datasets, without a token.

    We expect dataset/table without a scope and dataset/field_scope with a scope since field
    scopes are not evaluated.
    """
    response = api_client.get("/geosearch/catalogus/")
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
def test_catalogus_table_scope(api_client, dataset):
    """
    Test that the catalogus endpoint returns the expected datasets, with a token.

    Since a token is provided we also expect the dataset/table_scope to be returned.
    """
    token = build_jwt_token(["FP/MDW"])
    response = api_client.get(
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
def test_catalogus_geosearch_disabled(api_client, dataset_geosearch_disabled):
    """Test that the catalogus endpoint doesn't return datasets with geosearch disabled."""
    response = api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {"datasets": []}


@pytest.mark.django_db
def test_catalogus_dataset_scopes_without_token(api_client, dataset_scope):
    """
    Test that the catalogus endpoint doesn't return datasets with dataset scopes
    when no token is provided.
    """
    response = api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {"datasets": []}


@pytest.mark.django_db
def test_catalogus_dataset_scopes_with_token(api_client, dataset_scope):
    """
    Test that the catalogus endpoint returns datasets with dataset scopes when a token
    with the right scope is provided.
    """
    token = build_jwt_token(["FP/MDW"])
    response = api_client.get(
        "/geosearch/catalogus/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"datasets": ["dataset_scope/table", "dataset_scope/v1/table"]}


@pytest.mark.django_db
def test_catalogus_with_versions(api_client, dataset_versions):
    """
    Test that the catalogus endpoint returns the versioned datasets.
    """
    response = api_client.get("/geosearch/catalogus/")
    assert response.status_code == 200
    assert response.json() == {
        "datasets": [
            "dataset_versions/table",
            "dataset_versions/v1/table",
            "dataset_versions/v2/table",
        ]
    }
