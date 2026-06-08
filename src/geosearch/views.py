from adrf.decorators import api_view
from asgiref.sync import sync_to_async
from django.db import OperationalError
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from schematools.contrib.django.models import Dataset

from geosearch.registry import get_registry
from geosearch.search import GeosearchContext, get_features
from geosearch.serializers import GeosearchInputSerializer


@api_view(["GET"])
async def pulse(request):
    """
    Simple health probe.
    """
    return Response({"status": "OK"})


@api_view(["GET"])
async def health_check(request):
    """
    Verify connection to the database and that the service is running.
    """
    try:
        _ = await Dataset.objects.afirst()
    except OperationalError as e:
        raise APIException("Failed to connect to the database") from e
    return Response({"status": "OK", "database": "OK"})


@api_view(["GET"])
def catalogus(request):
    registry = get_registry()
    all_routes = registry.get_table_paths(scopes=frozenset(request.get_token_scopes))

    return JsonResponse(
        {
            "datasets": all_routes,
        }
    )


@api_view(["GET"])
async def geosearch(request):
    """
    Search endpoint for geospatial queries.
    Query params:
      - datasets: comma separated list of datasets
      - lat: latitude in WGS84
      - lon: longitude in WGS84
      - x: x coordinate in Rijksdriehoek
      - y: y coordinate in Rijksdriehoek
      - radius: radius in meters
      - limit: maximum number of results to return for each dataset
    """
    serializer = GeosearchInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if serializer.validated_data["use_rd"]:
        x = serializer.validated_data.get("x")
        y = serializer.validated_data.get("y")
    else:
        x = serializer.validated_data.get("lon")
        y = serializer.validated_data.get("lat")

    context = GeosearchContext(
        x=x,
        y=y,
        use_rd=serializer.validated_data["use_rd"],
        fields=serializer.validated_data.get("_fields", []),
        radius=serializer.validated_data.get("radius"),
        limit=serializer.validated_data.get("limit"),
    )
    # Get the tables to query based on the path(s)
    paths = serializer.validated_data.get("datasets", [])
    registry = await sync_to_async(get_registry)()
    tables = {}
    for path in paths:
        tables.update(registry.get_tables_by_path(path))

    return StreamingHttpResponse(
        get_features(tables, context),
        content_type="application/json",
    )
