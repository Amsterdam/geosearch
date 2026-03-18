import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def api_client() -> APIClient:
    api_client = APIClient()
    api_client.default_format = "json"  # instead of multipart
    return api_client
