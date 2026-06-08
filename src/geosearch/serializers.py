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
        if not data.get("x") and not data.get("y") and not data.get("lat") and not data.get("lon"):
            raise serializers.ValidationError(
                "No coordinates provided. Please provide both x/y or lat/lon coordinates."
            )

        if data.get("x") and data.get("y") and data.get("lat") and data.get("lon"):
            raise serializers.ValidationError("Either x/y or lat/lon must be provided, not both")

        if data.get("x") and data.get("y"):
            data["use_rd"] = True

        return data

    def validate_datasets(self, value: str) -> list[str]:
        return value.split(",")

    def validate__fields(self, value: str) -> list[str]:
        return value.split(",")
