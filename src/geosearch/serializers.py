from __future__ import annotations

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer(
    exclude_fields=("_fields",),
)
class GeosearchInputSerializer(serializers.Serializer):
    datasets = serializers.CharField(
        required=False,
        help_text="Dataset and/or subset name(s) to search in presented as comma separated list. "
        "The /catalogus/ endpoint gives a listing of the possible values.",
    )
    lat = serializers.FloatField(
        required=False,
        help_text="Latitude of coordinate to search for. Example value 52.372239620672204. "
        "Requires a complementing lon parameter.",
    )
    lon = serializers.FloatField(
        required=False,
        help_text="Longitude of coordinate to search for. Example value 4.900848228657843. "
        "Requires a complementing lat parameter.",
    )
    x = serializers.FloatField(
        required=False,
        help_text="X (rd) coordinate to search for. Example value 121848. "
        "Requires a complementing Y parameter.",
    )
    y = serializers.FloatField(
        required=False,
        help_text="Y (rd) coordinate to search for. Example value 487307. "
        "Requires a complementing X parameter.",
    )
    radius = serializers.IntegerField(
        required=False,
        default=0,
        help_text="The radius the search in approximate meters. The search is actually performed "
        "in fractions of degrees and does not take curvature and terrain into account.",
    )
    limit = serializers.IntegerField(required=False, help_text="The amount of results.")
    _fields = serializers.CharField(required=False)
    use_rd = serializers.HiddenField(default=False)

    def validate(self, data: dict) -> dict:
        has_x = data.get("x") is not None
        has_y = data.get("y") is not None
        has_lat = data.get("lat") is not None
        has_lon = data.get("lon") is not None

        has_rd = has_x or has_y
        has_wgs = has_lat or has_lon

        if not has_rd and not has_wgs:
            raise serializers.ValidationError(
                "No coordinates provided. Please provide both x/y or lat/lon coordinates."
            )

        if has_rd and has_wgs:
            raise serializers.ValidationError("Either x/y or lat/lon must be provided, not both")

        if has_rd and not (has_x and has_y):
            raise serializers.ValidationError("Both x and y must be provided together")

        if has_wgs and not (has_lat and has_lon):
            raise serializers.ValidationError("Both lat and lon must be provided together")

        data["use_rd"] = has_rd
        return data

    def validate_datasets(self, value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    def validate__fields(self, value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]
