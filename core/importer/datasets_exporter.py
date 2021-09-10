import json
import sys

from core.models import  Dataset
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO

logger = DaisyLogger(__name__)


class DatasetsExporter:
    def __init__(self, include_unpublished=False, objects=None):
        """
        objects would be Django object manager containing datasets to export,
        i.e.:
        objects = Dataset.objects.all()
        objects = Dataset.objects.filter(acronym='test')
        """
        self.include_unpublished = include_unpublished
        if objects is not None:
            self.objects = objects
        else:
            self.objects = None

    def set_objects(objects):
        self.objects = objects

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            logger.error('Dataset export failed')
            logger.error(str(e))
            result = False
        logger.info(f'Dataset export complete see file: {file_handle}')
        return result

    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        dataset_dicts = []
        if self.objects is not None:
            objects = self.objects
        else:
            objects = Dataset.objects.all()
        for dataset in objects:
            dataset_repr = str(dataset)
            logger.debug(f' * Exporting dataset: "{dataset_repr}"...')
            try:
                pd = dataset.to_dict()
                pd["source"] = settings.SERVER_URL
                dataset_dicts.append(pd)
            except Exception as e:
                logger.error(f'Export failed for dataset {dataset.title}')
                logger.error(str(e))
                if verbose:
                    import traceback
                    ex = traceback.format_exception(*sys.exc_info())
                    logger.error('\n'.join([e for e in ex]))
                if stop_on_error:
                    raise e
            logger.debug("   ... complete!")
        json.dump({
            "$schema": "https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/master/schemas/elu-dataset.json",
            "items": dataset_dicts}, buffer, indent=4)
        return buffer

