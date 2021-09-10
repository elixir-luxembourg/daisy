from functools import reduce
from operator import concat
from typing import List

from django.template.loader import render_to_string
from core.models import data_declaration

from core.models.dataset import Dataset
from core.models.data_declaration import DataDeclaration
from core.models.project import Project
from core.models.user import User


class Issue:
    def __init__(self,
            url: str,
            code: str,
            description: str,
            object_title: str) -> None:
        self.url = url
        self.object_title = object_title
        self.description = description
        self.code = code


class ReportParameters:
    """
    Better to use dataclass from dataclasses here
    but only once we move to Python 3.7
    """
    def __init__(self, 
                 projects: List[Project] = None,
                 datasets: List[Dataset] = None,
                 data_declarations: List[DataDeclaration] = None,
                 issues: List[Issue] = None) -> None:
        self.issues = issues
        self.datasets = datasets
        self.data_declarations = data_declarations
        self.projects = projects


class ReportParametersCollector:
    @classmethod
    def generate_for_user(cls, user: User):
        projects = Project.objects.filter(local_custodian__in=User)
        # TODO: What exactly needs to be collected here:
        # 1) datasets whose local_custodian is the User
        # 2) datasets linked to the project
        # 3) everything, 1 + 2 

        datasets = Dataset.objects.filter(local_custodian__in=User)

        data_declarations_list = [dataset.data_declarations for dataset in datasets]
        data_declarations_with_repetitions = reduce(concat, data_declarations_list)
        data_declarations = list(set(data_declarations_with_repetitions))

        # TODO: Generate Issues
        issues = None
        
        return ReportParameters(projects, datasets, data_declarations, issues)


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
