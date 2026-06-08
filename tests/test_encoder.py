import json

import pytest
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

from geosearch.encoder import GeosearchResultEncoder


def test_json_encoder():
    data = {
        "distance": Distance(km=1),
    }
    assert json.dumps(data, cls=GeosearchResultEncoder) == '{"distance": 1000.0}'


def test_json_encoder_calls_super():
    data = {"point": Point(1, 1)}
    with pytest.raises(TypeError):
        json.dumps(data, cls=GeosearchResultEncoder)
