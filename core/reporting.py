
from typing import List

from django.template.loader import render_to_string

from core.models.project import Project
from core.models.dataset import Dataset
from core.models.data_declaration import DataDeclaration


class ReportParameters:
    """
    Better to use dataclass from dataclasses here
    but only once we move to Python 3.7
    """
    def __init__(self, 
                 projects: List[Project] = None,
                 datasets: List[Dataset] = None,
                 data_declarations: List[DataDeclaration] = None,
                 issues: List = None) -> None:
        self.issues = issues
        self.datasets = datasets
        self.data_declarations = data_declarations
        self.projects = projects


class ReportRenderer:
    def __init__(self, 
                 projects: List[Project] = None,
                 datasets: List[Dataset] = None,
                 data_declarations: List[DataDeclaration] = None,
                 issues: List = None) -> None:
        self.issues = issues
        self.datasets = datasets
        self.data_declarations = data_declarations
        self.projects = projects

    @classmethod
    def create(cls, report_parameters: ReportParameters):
        return cls(
            report_parameters.projects,
            report_parameters.datasets,
            report_parameters.data_declarations,
            report_parameters.issues
        )

    def render(self):
        context = {
            'projects': self.projects,
            'datasets': self.datasets,
            'data_declarations': self.data_declarations,
            'issues': self.issues
        }
        return render_to_string('core/templates/report_email.html', context)
