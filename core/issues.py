from typing import List

from django.urls import reverse

from core.models.data_declaration import DataDeclaration
from core.models.project import Project
from core.models.dataset import Dataset
from core.utils import get_absolute_uri


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


def find_issues_in_dataset(dataset: Dataset) -> List[Issue]:
    issues = []
    local_url = reverse('dataset', args=[str(dataset.id)])
    url = get_absolute_uri(local_url)
    
    if dataset.legal_basis_definitions.count() == 0:
        issues.append(Issue(url, '[D-1]', 'Missing legal bases for a dataset', dataset.title))

    if dataset.data_declarations.count() == 0:
        issues.append(Issue(url, '[D-2]', 'No data declarations for a dataset', dataset.title))

    if dataset.data_locations.count() == 0:
        issues.append(Issue(url, '[D-3]', 'No storage locations for a dataset', dataset.title))

    if dataset.accesses.count() == 0:
        issues.append(Issue(url, '[D-4]', 'No access specified for a dataset', dataset.title))

    if dataset.sensitivity is None:
        issues.append(Issue(url, '[D-5]', 'No sensitivity class for a dataset', dataset.title))

    return issues

def find_issues_in_project(project: Project) -> List[Issue]:
    issues = []
    local_url = reverse('project', args=[str(project.id)])
    url = get_absolute_uri(local_url)

    if project.datasets.count() == 0:
        issues.append(Issue(url, '[P-1]', 'No dataset in a project', project.acronym))

    if project.has_erp == False and (project.erp_notes is None or len(project.erp_notes) == 0):
        issues.append(Issue(url, '[P-2]', 'No ERP approval and no ERP notes', project.acronym))

    #If a project is marked as having Ethics,a document of type ethics approval should be uploaded
    if project.has_erp:
        ethics_approval_docs = project.legal_documents.all().filter(domain_type = 'ethics_approval')
        if len(ethics_approval_docs) < 1:
            issues.append(Issue(url, '[P-3]', 'Projet has an ERP approval but ethics approval document is not uploaded', project.acronym))

    # Does the project have a data classification and a DPIA attachment.
    dpia_docs = project.legal_documents.all().filter(domain_type = 'data_protection_impact_assessment')
    if len(dpia_docs) < 1:
        issues.append(Issue(url, '[P-4]', 'DPIA not present', project.acronym))

    return issues

def find_issues_in_datadeclaration(data_declaration: DataDeclaration) -> List[Issue]:
    issues = []
    local_url = reverse('data_declaration', args=[str(data_declaration.id)])
    url = get_absolute_uri(local_url)

    # Storage end date is filled in. If not, there should be explanaition
    if data_declaration.end_of_storage_duration is None and data_declaration.storage_duration_criteria is None:
        issues.append(Issue(url, '[DD-1]', 'No storage end date or storage duration criteria recorded', data_declaration.title))

    return issues

def _accumulate_results(objects, func):
    results = []
    for obj in objects:
        results = results + func(obj)
    return results

def find_issues_in_datasets(datasets: List[Dataset]) -> List[Issue]:
    return _accumulate_results(datasets, find_issues_in_dataset)

def find_issues_in_projects(projects: List[Project]) -> List[Issue]:
    return _accumulate_results(projects, find_issues_in_project)

def find_issues_in_datadeclarations(data_declarations: List[DataDeclaration]) -> List[Issue]:
    return _accumulate_results(data_declarations, find_issues_in_datadeclaration)
