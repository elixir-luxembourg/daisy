import json
import sys

from core.models import Dataset, Exposure
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO
from urllib.parse import urljoin

JSONSCHEMA_BASE_REMOTE_URL = getattr(settings, "IMPORT_JSON_SCHEMAS_URI")

logger = DaisyLogger(__name__)


class DatasetsExporter:
    def __init__(self, objects=None, endpoint_id=-1, include_unpublished=False):
        self.include_unpublished = include_unpublished
        """
        objects would be Django object manager containing datasets to export,
        i.e.:
        objects = Dataset.objects.all()
        objects = Dataset.objects.filter(acronym='test')
        """
        if objects is not None:
            self.objects = objects
        else:
            self.objects = None
        self.endpoint_id = endpoint_id

    def set_objects(self, objects):
        self.objects = objects

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            logger.error("Dataset export failed")
            logger.error(str(e))
            result = False
        logger.info(f"Dataset export complete see file: {file_handle}")
        return result

    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        dataset_dicts = []
        if self.objects is not None:
            objects = self.objects
        else:
            objects = Dataset.objects.all()
        if not self.include_unpublished:
            objects = objects.filter(
                exposures__endpoint__id=self.endpoint_id
            ).distinct()  # we have deprecated exposures for one dataset
        for dataset in objects:
            dataset_repr = str(dataset)
            logger.debug(f' * Exporting dataset: "{dataset_repr}"...')
            try:
                pd = dataset.to_dict()
                pd["source"] = settings.SERVER_URL
                if not self.include_unpublished:
                    exposure = Exposure.objects.order_by("-deprecated_at").filter(
                        dataset=dataset, endpoint_id=self.endpoint_id
                    )[0]
                    pd["form_id"] = exposure.form_id
                    pd["deprecated"] = exposure.is_deprecated
                    pd["deprecation_date"] = (
                        exposure.deprecated_at.isoformat(timespec="seconds")
                        if exposure.deprecated_at
                        else None
                    )
                    pd["released_date"] = (
                        exposure.added.isoformat(timespec="seconds")
                        if exposure.added
                        else None
                    )
                    pd["deprecation_notes"] = exposure.deprecation_reason
                dataset_dicts.append(pd)
            except Exception as e:
                logger.error(f"Export failed for dataset {dataset.title}")
                logger.error(str(e))
                if verbose:
                    import traceback

                    ex = traceback.format_exception(*sys.exc_info())
                    logger.error("\n".join([e for e in ex]))
                if stop_on_error:
                    raise e
            logger.debug("   ... complete!")

        json.dump(
            {
                "$schema": urljoin(JSONSCHEMA_BASE_REMOTE_URL, "elu-dataset.json"),
                "items": dataset_dicts,
            },
            buffer,
            indent=4,
        )
        return buffer
