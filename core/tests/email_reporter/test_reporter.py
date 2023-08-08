from typing import cast

from django.conf import settings
from django.db.models.query import QuerySet

from core.issues import Issue
from core.models import Project, data_declaration
from core.reporting import cast_to_queryset, cast_to_issue_list, get_users_to_receive_emails
from core.reporting import ReportParameters, ReportParametersCollector, ReportRenderer
from test import factories


def test_cast_to_queryset():
    assert cast_to_queryset(None, Project) is None

    project = factories.ProjectFactory.create(acronym='test1', title='test1')
    assert type(cast_to_queryset(project, Project)) == QuerySet

    project2 = factories.ProjectFactory.create(acronym='test2', title='test2')
    assert type(cast_to_queryset([project, project2], Project)) == QuerySet

    assert type(cast_to_queryset(Project.objects.all(), Project)) == QuerySet
    assert type(cast_to_queryset(Project.objects, Project)) == QuerySet
    assert type(cast_to_queryset(Project.objects.get(acronym='test2'), Project)) == QuerySet


def test_cast_to_issue_list():
    issue = Issue('https://a.com', '1', 'desc', 'title')
    assert cast_to_issue_list(None) is None
    assert type(cast_to_issue_list(issue)) == list
    assert issue in cast_to_issue_list(issue)
    

def test_report_parameters():
    """Ensure that all of these don't fail"""
    project = factories.ProjectFactory.create(acronym='test', title='test')
    project.save()

    empty_report_parameters = ReportParameters()
    report_parameters_with_single_instances = ReportParameters(project)
    report_parameters_with_list_of_instances = ReportParameters([project])
    report_parameters_with_queryset = ReportParameters(Project.objects.filter(title='test'))
    report_parameters_with_queryset2 = ReportParameters(Project.objects.get(title='test'))
    report_parameters_with_objects = ReportParameters(Project.objects.filter(title='test').all())

def test_report_renderer():
    """Ensure that correct HTML is being output"""
    PROJECT_ACRONYM = 'SomethingRandomAcronym2'
    PROJECT_TITLE = 'AnotherTitle2'
    USER_NAME = 'Doy'

    user1 = factories.UserFactory.create(first_name=USER_NAME, last_name=USER_NAME)
    user1.save()
    project = factories.ProjectFactory.create(acronym=PROJECT_ACRONYM, title=PROJECT_TITLE)
    project.local_custodians.add(user1)
    project.save()
    dataset = factories.DatasetFactory.create(project=project)
    dataset.save()

    list_of_projects = list(Project.objects.filter(title=PROJECT_TITLE).all())
    params = ReportParameters(list_of_projects)
    report_renderer = ReportRenderer(params)

    rendered_html = report_renderer.render_html()
    _ = report_renderer.render_txt()
    assert PROJECT_ACRONYM in rendered_html
    assert PROJECT_TITLE in rendered_html

def test_report_collector():
    """Ensure that the correct entities are accepted"""
    PROJECT_ACRONYM = 'SomethingRandomAcronym'
    PROJECT_TITLE = 'AnotherTitle'

    user1 = factories.UserFactory.create(first_name='Julia', last_name='Crayon')
    user1.save()
    project = factories.ProjectFactory.create(acronym=PROJECT_ACRONYM, title=PROJECT_TITLE)
    project.local_custodians.add(user1)
    project.save()

    dataset = factories.DatasetFactory.create(project=project)
    dataset.local_custodians.add(user1)
    dataset.save()

    data_declaration = factories.DataDeclarationFactory.create(dataset=dataset)
    data_declaration.save()

    params = ReportParametersCollector.generate_for_user(user1)
    assert len(params.projects) == 1
    assert len(params.issues) > 0
    assert len(params.datasets) == 1
    assert len(params.data_declarations) == 1

    assert params.projects[0].acronym == PROJECT_ACRONYM

def test_get_users_to_receive_emails():
    previous_value = getattr(settings, 'EMAIL_REPORTS_ENABLED', None)

    user1 = factories.UserFactory.create(first_name='Daria', last_name='Crayon', email='daria@crayon.com', should_receive_email_reports=True)
    user1.save()

    user2 = factories.UserFactory.create(first_name='Adam', last_name='Crayon', email='adam@crayon.com', should_receive_email_reports=False)
    user2.save()

    user3 = factories.UserFactory.create(first_name='Bob', last_name='Malrey', email='bobmalrey.com', should_receive_email_reports=True)
    user3.save()

    setattr(settings, 'EMAIL_REPORTS_ENABLED', False)
    assert len(get_users_to_receive_emails()) == 0
    assert len(get_users_to_receive_emails(True)) > 0

    setattr(settings, 'EMAIL_REPORTS_ENABLED', True)
    assert len(get_users_to_receive_emails()) > 0
    users = get_users_to_receive_emails(True)
    assert len(users) > 0
    assert user1 in users
    assert user2 not in users
    assert user3 not in users

    setattr(settings, 'EMAIL_REPORTS_ENABLED', previous_value)
