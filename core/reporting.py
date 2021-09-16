from functools import reduce
from operator import concat
from typing import List, Type, Union

from django.conf import settings
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.models.manager import Manager
from django.template.loader import render_to_string

from core.models.dataset import Dataset
from core.models.data_declaration import DataDeclaration
from core.models.project import Project
from core.models.user import User
from notification.email_sender import send_the_email


def cast_to_queryset(object: Union[Model, List[Model], QuerySet], klass: Type = None) -> QuerySet:
    """
    Casts the parameter to a queryset.
    Accepts:
     - the object (of Model)
     - a list of objects
     - a Queryset (e.g. Project.objects.all())
     - a Manager (e.g. Project.objects)
    """
    if object is None:
        return None
    if klass is None:
        raise TypeError(f'`klass` parameter missing!')    
    if type(object) == klass:
        return klass.objects.filter(id=object.id)
    if type(object) == list:
        ids = [x.id for x in object]
        return klass.objects.filter(id__in=ids)
    if type(object) == QuerySet:
        return object
    if type(object) == Manager:
        return object.all()
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
                 projects: Union[Project, List[Project], QuerySet] = None,
                 datasets: Union[Dataset, List[Dataset], QuerySet] = None,
                 data_declarations: Union[DataDeclaration, List[DataDeclaration], QuerySet] = None,
                 issues: Union[Issue, List[Issue], QuerySet] = None) -> None:
        self.issues = cast_to_queryset(issues, Issue)
        self.datasets = cast_to_queryset(datasets, Dataset)
        self.data_declarations = cast_to_queryset(data_declarations, DataDeclaration)
        self.projects = cast_to_queryset(projects, Project)


class ReportParametersCollector:
    @classmethod
    def generate_for_user(cls, user: User) -> ReportParameters:
        """
        Generates the `ReportParameters` containing given User's entities -
        projects, datasets, data declarations and issues.
        """
        projects = Project.objects.filter(local_custodians__id=user.id)
        # TODO: What exactly needs to be collected here:
        # 1) datasets whose local_custodian is the User
        # 2) datasets linked to the project
        # 3) everything, 1 + 2 

        datasets = Dataset.objects.filter(local_custodians__id=user.id)

        data_declarations_list = [dataset.data_declarations.all() for dataset in datasets]
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

    def render_html(self) -> str:
        return self._render('report_email.html')

    def render_txt(self) -> str:
        return self._render('report_email.txt')
    
    def _render(self, template_name) -> str:
        context = {
            'projects': self.projects,
            'datasets': self.datasets,
            'data_declarations': self.data_declarations,
            'issues': self.issues
        }
        return render_to_string(template_name, context)

def get_users_to_receive_emails(force=False) -> List[User]:
    should_continue = getattr(settings, 'EMAIL_REPORTS_ENABLED', False)
    if force or should_continue:
        return User.objects.filter(email__contains='@')
    else:
        return []

def generate_and_send_reports(force=False) -> None:
    list_of_users = get_users_to_receive_emails(force)

    for user in list_of_users:
        generate_and_send_report_to(user)

def generate_and_send_report_to(user: User) -> None:
    report_params = ReportParametersCollector.generate_for_user(user)
    html_contents = ReportRenderer(report_params).render_html()
    txt_contents = ReportRenderer(report_params).render_txt()
    send_the_email(
        settings.EMAIL_DONOTREPLY,
        user.email,
        'Report',
        txt_contents,
        html_contents
    )