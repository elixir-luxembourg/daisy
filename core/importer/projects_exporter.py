import json
import sys

from core.models import Project
from core.utils import DaisyLogger
from django.conf import settings
from io import StringIO


logger = DaisyLogger(__name__)


class ProjectsExporter:
    def __init__(self, objects=None):
        """
        objects would be Django obejct manager containing projects to export,
        i.e.:
        objects = Project.objects.all()
        objects = Project.objects.filter(acronym='test')
        """
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
            logger.error('Project export failed')
            logger.error(str(e))
            result = False
        logger.info(f'Project export complete see file: {file_handle}')
        return result


    def export_to_buffer(self, buffer, stop_on_error=False, verbose=False):
        project_dicts = []

        if self.objects is not None:
            objects = self.objects
        else:
            objects = Project.objects.all()

        for project in objects:
            logger.debug(f' * Exporting project: "{project.acronym}"...')
            try:
                pd = project.to_dict()
                pd["source"] = settings.SERVER_URL
                project_dicts.append(pd)
            except Exception as e:
                project_repr = str(project)
                logger.error(f'Export failed for project f{project_repr}')
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


