import logging

from schematools.contrib.django.models import Dataset

logger = logging.getLogger(__name__)


async def get_geosearch_datasets() -> list[Dataset]:
    db_datasets = Dataset.objects.all()

    return [ds async for ds in db_datasets if ds.schema.has_an_available_geosearch_version]
