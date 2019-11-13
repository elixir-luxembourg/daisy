import json
import sys

from core.models import Project
from core.utils import DaisyLogger
from django.conf import settings

logger = DaisyLogger(__name__)


class ProjectsExporter:

    def export_to_file(self, file, stop_on_error=False, verbose=False):

        logger.info('Export started ')
        result = True

        project_dicts = []
        projects = Project.objects.all()

        for project in projects:
            logger.debug(' * Exporting project: "{}"...'.format(project.acronym))
            try:


                pd = project.to_dict()
                pd["source"] = settings.SERVER_URL
                project_dicts.append(pd)

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
            "$schema": "https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/elu-project.json",
            "items": project_dicts}, file , indent=4)

        logger.info('Exported  {} projects to file: {}'.format(len(project_dicts), file))

        return result


