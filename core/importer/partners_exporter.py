import json
import sys

from core.models import Partner
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO
from urllib.parse import urljoin

JSONSCHEMA_BASE_REMOTE_URL = getattr(settings, 'IMPORT_JSON_SCHEMAS_URI')

logger = DaisyLogger(__name__)


class PartnersExporter:
    def __init__(
            self,
            include_unpublished=False):
        self.include_unpublished = include_unpublished

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            logger.error('Partner export failed')
            logger.error(str(e))
            result = False

        logger.info(f'Partner export complete see file: {file_handle}')
        return result


    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):

            partner_dicts = []
            partners = Partner.objects.all()
            for partner in partners:
                logger.debug(f' * Exporting partner: "{partner.name}"...')
                if partner.is_published or self.include_unpublished:
                    try:
                        pd = partner.to_dict()
                        pd["source"] = settings.SERVER_URL
                        partner_dicts.append(pd)

                    except Exception as e:
                        logger.error('Export failed')
                        logger.error(str(e))
                        if verbose:
                            import traceback
                            ex = traceback.format_exception(*sys.exc_info())
                            logger.error('\n'.join([e for e in ex]))
                        if stop_on_error:
                            raise e
                    logger.debug("   ... complete!")
                else:
                    logger.debug(f' "{partner.name}" is not published, it can not be exported')
            json.dump({
                "$schema": urljoin(JSONSCHEMA_BASE_REMOTE_URL, 'elu-institution.json'),
                "items": partner_dicts}, buffer , indent=4)
            return buffer


