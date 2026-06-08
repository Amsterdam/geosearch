import json
from typing import Any

from django.contrib.gis.measure import Distance


class GeosearchResultEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Distance):
            return o.m
        return super().default(o)
