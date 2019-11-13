import json
import sys

from core.models import Partner
from core.utils import DaisyLogger
from django.conf import settings

logger = DaisyLogger(__name__)


class PartnersExporter:

    def export_to_file(self, file, stop_on_error=False, verbose=False):

        logger.info('Export started ')
        result = True

        partner_dicts = []
        partners = Partner.objects.all()

        for partner in partners:
            logger.debug(' * Exporting partner: "{}"...'.format(partner.name))
            try:
                pd = partner.to_dict()
                pd["source"] = settings.SERVER_URL
                partner_dicts.append(pd)

            except Exception as e:
                logger.error('Import failed')
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
            "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-partner.json",
            "items": partner_dicts}, file , indent=4)

        logger.info('Exported  {} partners to file: {}'.format(len(partner_dicts), file))

        return result


