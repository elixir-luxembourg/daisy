from core.reporting import ReportParameters, ReportParametersCollector, ReportRenderer

from core.models import Project
from test import factories


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

    rendered_html = report_renderer.render()
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

    params = ReportParametersCollector.generate_for_user(user1)
    assert len(params.projects) == 1
    assert params.issues is None
    assert len(params.datasets) == 0
    assert len(params.data_declarations) == 0

    assert params.projects[0].acronym == PROJECT_ACRONYM
