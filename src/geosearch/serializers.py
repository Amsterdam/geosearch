from __future__ import annotations

from rest_framework import serializers


class GeosearchInputSerializer(serializers.Serializer):
    datasets = serializers.CharField(required=False)
    lat = serializers.FloatField(required=False)
    lon = serializers.FloatField(required=False)
    x = serializers.FloatField(required=False)
    y = serializers.FloatField(required=False)
    radius = serializers.IntegerField(required=False, default=0)
    limit = serializers.IntegerField(required=False)
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
