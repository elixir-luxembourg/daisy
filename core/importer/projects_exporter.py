import json
import sys

from core.models import Project
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO


logger = DaisyLogger(__name__)


class ProjectsExporter:

    def export_to_file(self, file_handle, stop_on_error=False, verbose=False):
        result = True
        try:
            buffer = self.export_to_buffer(StringIO())
            print(buffer.getvalue(), file=file_handle)
        except Exception as e:
            logger.error('Project export failed')
            logger.error(str(e))
            result = False
        logger.info('Project export complete see file: {}'.format(file_handle))
        return result


    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
            project_dicts = []
            projects = Project.objects.all()
            for project in projects:
                logger.debug(' * Exporting project: "{}"...'.format(project.acronym))
                try:
                    pd = project.to_dict()
                    pd["source"] = settings.SERVER_URL
                    project_dicts.append(pd)
                except Exception as e:
                    logger.error('Export failed for project {}'.format(project.__str__()))
                    logger.error(str(e))
                    if verbose:
                        import traceback
                        ex = traceback.format_exception(*sys.exc_info())
                        logger.error('\n'.join([e for e in ex]))
                    if stop_on_error:
                        raise e
                logger.debug("   ... complete!")
            json.dump({
                "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-project.json",
                "items": project_dicts}, buffer , indent=4)
            return buffer


