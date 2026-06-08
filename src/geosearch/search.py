import json
from typing import Any

from django.conf import settings
from django.contrib.gis.db.models.functions import Centroid, Distance, Transform
from django.contrib.gis.geos import Point
from django.db.models import F, Q, Value
from django.db.models.functions import Concat, Now
from schematools.contrib.django.models import DynamicModel
from schematools.naming import to_snake_case
from schematools.types import DatasetFieldSchema

from geosearch.encoder import GeosearchResultEncoder


class GeosearchContext:
    tables = []

    def __init__(
        self,
        x: float,
        y: float,
        use_rd: bool,
        fields: list[str],
        radius: int | None = None,
        limit: int | None = None,
    ):
        self.x = x
        self.y = y
        self.use_rd = use_rd
        self.fields = fields
        self.radius = radius
        self.limit = limit


class GeosearchTableQuery:
    def __init__(self, table: DynamicModel, path: str, context: GeosearchContext):
        self.table = table
        self.table_schema = table.table_schema()
        self.context = context

        self.id_field = self._get_id_field()
        self.display_field = (
            self.table_schema.display_field if self.table_schema.display_field else self.id_field
        )
        self.main_geometry_field = self.table_schema.main_geometry_field

        self.default_properties = (self.id_field.db_name, "display", "uri", "opr_type", "distance")

        self.api_path = path
        self.table_type = f"{self.table_schema.dataset.id}/{self.table_schema.id}"

    def _get_id_field(self) -> DatasetFieldSchema:
        if self.table_schema.is_temporal:
            field_name = next(
                iter(set(self.table_schema.identifier) - {self.table_schema.temporal.identifier})
            )
        else:
            field_name = self.table_schema.identifier[0]
        return self.table_schema.get_field_by_id(field_name)

    def _get_fields(self) -> list[str]:
        # Only request additional fields if they exist on the model
        additional_fields = [
            to_snake_case(f)
            for f in self.context.fields
            if to_snake_case(f) in [x.name for x in self.table._meta.get_fields()]
        ]
        return [
            to_snake_case(self.display_field.db_name),
            self.main_geometry_field.db_name,
            self.id_field.db_name,
            *additional_fields,
        ]

    def _get_queryset(self):
        queryset = self.table.objects.all()

        # Add required fields to each record for easy extraction
        annotations: dict[str, Any] = {
            "display": F(self.table_schema.display_field.db_name),
            "uri": Concat(Value(settings.DSO_API_BASE_URL), Value(self.api_path)),
        }

        # Add distance to the coordinates to the result
        if any(
            geometry_type in self.main_geometry_field.type.upper()
            for geometry_type in ["POLYGON", "MULTIPOLYGON"]
        ):
            # For polygons get the centroid as distance to the coordinate
            annotations["distance"] = Distance(
                Centroid(self.main_geometry_field.db_name), self._get_point_from_context()
            )
        else:
            annotations["distance"] = Distance(
                self.main_geometry_field.db_name, self._get_point_from_context()
            )

        queryset = queryset.annotate(**annotations)

        filter_kwargs = {
            f"{self.main_geometry_field.db_name}__dwithin": (
                self._get_point_from_context(),
                self.context.radius,
            )
        }

        queryset = queryset.filter(**filter_kwargs)

        if self.table_schema.is_temporal:
            # For temporal tables, we query the current temporal record
            start = self.table_schema.temporal.dimensions["geldigOp"].start.db_name
            end = self.table_schema.temporal.dimensions["geldigOp"].end.db_name

            queryset = queryset.filter(
                Q(**{f"{start}__lt": Now()})
                & (Q(**{f"{end}__isnull": True}) | Q(**{f"{end}__gt": Now()}))
            )

        queryset = queryset.only(*self._get_fields()).order_by("distance")

        if self.context.limit:
            return queryset[: self.context.limit]

        return queryset

    def _get_point_from_context(self) -> Point | Transform:
        """Return a point in WGS84, transforming from RD if necessary."""
        if self.context.use_rd:
            return Transform(Point(self.context.x, self.context.y, srid=28992), 4326)
        return Point(self.context.x, self.context.y, srid=4326)

    async def get_features(self):
        async for row in self._get_queryset():
            data = {
                "properties": {
                    **{
                        prop: getattr(row, prop)
                        for prop in self.default_properties
                        if hasattr(row, prop)
                    },
                    **{
                        field: getattr(row, to_snake_case(field))
                        for field in self.context.fields
                        if hasattr(row, to_snake_case(field))
                    },
                    "type": self.table_type,
                }
            }

            # For temporal tables we want the identifier field and not the raw id
            if self.table_schema.is_temporal:
                data["properties"]["id"] = getattr(row, self.id_field.db_name)

            yield data


async def get_features(tables: dict[str, DynamicModel], context: GeosearchContext):
    """
    Return all features for the requested tables as an async generator
    """
    first_item = True
    yield '{"type": "FeatureCollection", "features": ['
    for path, table in tables.items():
        query = GeosearchTableQuery(table, path, context)
        features = query.get_features()
        async for row in features:
            if first_item:
                first_item = False
            else:
                yield ","
            yield json.dumps(row, cls=GeosearchResultEncoder)
    yield "]}"
