import json
import sys

from core.models import  Dataset
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO

logger = DaisyLogger(__name__)


class DatasetsExporter:

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            logger.error('Dataset export failed')
            logger.error(str(e))
            result = False
        logger.info('Dataset export complete see file: {}'.format(file_handle))
        return result



    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        dataset_dicts = []
        datasets = Dataset.objects.all()
        for dataset in datasets:
            logger.debug(' * Exporting dataset: "{}"...'.format(dataset.__str__()))
            try:
                pd = dataset.to_dict()
                pd["source"] = settings.SERVER_URL
                dataset_dicts.append(pd)
            except Exception as e:
                logger.error('Export failed for dataset {}'.format(dataset.title))
                logger.error(str(e))
                if verbose:
                    import traceback
                    ex = traceback.format_exception(*sys.exc_info())
                    logger.error('\n'.join([e for e in ex]))
                if stop_on_error:
                    raise e
            logger.debug("   ... complete!")
        json.dump({
            "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-dataset.json",
            "items": dataset_dicts}, buffer, indent=4)
        return buffer

