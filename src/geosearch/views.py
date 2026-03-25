from adrf.decorators import api_view
from asgiref.sync import sync_to_async
from django.db import OperationalError
from django.http import JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from schematools.contrib.django.models import Dataset
from schematools.naming import to_snake_case
from schematools.types import DatasetSchema

from geosearch.datasets import get_geosearch_datasets


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
        _ = Dataset.objects.afirst()
    except OperationalError as e:
        raise APIException("Failed to connect to the database") from e
    return Response({"status": "OK", "database": "OK"})


@api_view(["GET"])
async def catalogus(request):
    datasets = await get_geosearch_datasets()
    all_routes = []
    for dataset in datasets:
        filtered_dataset = await sync_to_async(
            DatasetSchema.filter_on_scopes, thread_sensitive=True
        )(dataset.schema, request.get_token_scopes)

        for vmajor, version in filtered_dataset.versions.items():
            if not version.enable_geosearch:
                continue
            for table in version.get_tables():
                if table.has_geometry_fields:
                    if version.is_default:
                        all_routes.append(
                            f"{to_snake_case(dataset.schema.id)}/{to_snake_case(table.id)}"
                        )
                    all_routes.append(
                        f"{to_snake_case(dataset.schema.id)}/{vmajor}/{to_snake_case(table.id)}"
                    )

    data = {
        "datasets": all_routes,
    }

    return JsonResponse(data)
