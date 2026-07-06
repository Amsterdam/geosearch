import pytest
from rest_framework import serializers

from geosearch.serializers import GeosearchInputSerializer


def test_validation_no_coordinates():
    data = {
        "datasets": "dataset",
    }
    serializer = GeosearchInputSerializer(data=data)
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    assert (
        serializer.errors["non_field_errors"][0]
        == "No coordinates provided. Please provide both x/y or lat/lon coordinates."
    )


def test_validation_both_coordinates():
    data = {
        "datasets": "dataset",
        "x": 1,
        "y": 1,
        "lat": 1,
        "lon": 1,
    }
    serializer = GeosearchInputSerializer(data=data)
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    assert (
        serializer.errors["non_field_errors"][0]
        == "Either x/y or lat/lon must be provided, not both"
    )


def test_validation_one_of_x_y():
    data = {
        "datasets": "dataset",
        "x": 1,
    }
    serializer = GeosearchInputSerializer(data=data)
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    assert serializer.errors["non_field_errors"][0] == "Both x and y must be provided together"


def test_validation_one_of_lat_lon():
    data = {
        "datasets": "dataset",
        "lat": 1,
    }
    serializer = GeosearchInputSerializer(data=data)
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    assert serializer.errors["non_field_errors"][0] == "Both lat and lon must be provided together"
