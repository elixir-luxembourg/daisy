from functools import reduce
from operator import concat
from typing import List, Type, Union

from django.db.models import Model
from django.db.models.query import QuerySet
from django.template.loader import render_to_string

from core.models.dataset import Dataset
from core.models.data_declaration import DataDeclaration
from core.models.project import Project
from core.models.user import User


def ensure_queryset(object: Model, klass: Type):
    if object is None:
        return None
    if type(object) == klass:
        return klass.objects.get(id=object.id)
    if type(object) == list:
        ids = [x.id for x in object]
        return klass.objects.filter(id__in=ids)
    if type(object) == QuerySet:
        return object
    class_name = object.__class__.__name__
    raise TypeError(f'Unrecognised class: {class_name}!')
        

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
                 projects: Union[Project, List[Project]] = None,
                 datasets: Union[Dataset, List[Dataset]] = None,
                 data_declarations: Union[DataDeclaration, List[DataDeclaration]] = None,
                 issues: Union[Issue, List[Issue]] = None) -> None:
        self.issues = ensure_queryset(issues, Issue)
        self.datasets = ensure_queryset(datasets, Dataset)
        self.data_declarations = ensure_queryset(data_declarations, DataDeclaration)
        self.projects = ensure_queryset(projects, Project)


class ReportParametersCollector:
    @classmethod
    def generate_for_user(cls, user: User):
        projects = Project.objects.filter(local_custodians__id=user.id)
        # TODO: What exactly needs to be collected here:
        # 1) datasets whose local_custodian is the User
        # 2) datasets linked to the project
        # 3) everything, 1 + 2 

        datasets = Dataset.objects.filter(local_custodians__id=user.id)

        data_declarations_list = [dataset.data_declarations for dataset in datasets]
        if len(data_declarations_list) == 0:
            data_declarations = []
        else:
            data_declarations_with_repetitions = reduce(concat, data_declarations_list)
            data_declarations = list(set(data_declarations_with_repetitions))

        # TODO: Generate Issues
        issues = None
        
        return ReportParameters(projects, datasets, data_declarations, issues)


class ReportRenderer:
    def __init__(self, report_parameters: ReportParameters) -> None:    
        self.issues = report_parameters.issues
        self.datasets = report_parameters.datasets
        self.data_declarations = report_parameters.data_declarations
        self.projects = report_parameters.projects

    def render(self):
        context = {
            'projects': self.projects,
            'datasets': self.datasets,
            'data_declarations': self.data_declarations,
            'issues': self.issues
        }
        return render_to_string('report_email.html', context)
