import json
import sys

from core.models import  Dataset
from core.utils import DaisyLogger
from django.conf import settings

logger = DaisyLogger(__name__)


class DatasetsExporter:

    def export_to_file(self, file, stop_on_error=False, verbose=False):

        logger.info('Export started ')
        result = True

        dataset_dicts = []
        datasets = Dataset.objects.all()

        for dataset in datasets:
            logger.debug(' * Exporting dataset: "{}"...'.format(dataset.title))
            try:
                pd = dataset.to_dict()
                pd["source"] = settings.SERVER_URL
                dataset_dicts.append(pd)
            except Exception as e:
                logger.error('Export failed')
                logger.error(str(e))
                if verbose:
                    import traceback
                    ex = traceback.format_exception(*sys.exc_info())
                    logger.error('\n'.join([e for e in ex]))
                if stop_on_error:
                    raise e
                result = False
            logger.debug("   ... complete!")

        json.dump({
            "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-dataset.json",
            "items": dataset_dicts}, file , indent=4)

        logger.info('Exported  {} partners to file: {}'.format(len(dataset_dicts), file))

        return result


