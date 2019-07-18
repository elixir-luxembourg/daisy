from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

from core import constants
from .utils import CoreModel, COMPANY


class Project(CoreModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = (
            (constants.Permissions.ADMIN.value, 'Responsible of the project'),
            (constants.Permissions.EDIT.value, 'Edit the project'),
            (constants.Permissions.DELETE.value, 'Delete the project'),
            (constants.Permissions.VIEW.value, 'View the project'),
            (constants.Permissions.PROTECTED.value, 'View the protected elements'),
        )

    class AppMeta:
        help_text = "Projects are time-limited research activities with associated documentation on ethical, " \
                    "legal and administrative processes followed for their setup."

    acronym = models.CharField(blank=False,
                               null=False,
                               verbose_name='Acronym',
                               unique=True,
                               max_length=200,
                               help_text='Acronym is the short project name.')

    cner_notes = models.TextField(verbose_name='National ethics approval notes',
                                  default='',
                                  help_text='Provide notes on national ethics approval. If it does not exist, please state justifications here.',
                                  blank=True,
                                  null=True)

    contacts = models.ManyToManyField('core.Contact',
                                      related_name='projects',
                                      verbose_name='Contact persons',
                                      help_text='Contacts are project related people other than local personnel e.g. Project Officer at the European Commission can be recorded as a Contact.',
                                      blank=True)

    comments = models.TextField(verbose_name='Other comments',
                                blank=True,
                                null=True,
                                help_text='Any remarks other than the project description can be provided here.')

    company_personnel = models.ManyToManyField('core.User',
                                               related_name='projects',
                                               verbose_name='{}''s personnel'.format(COMPANY),
                                               help_text='Please select local staff that is part of this project.',
                                               blank=True)

    description = models.TextField(verbose_name='Lay summary',
                                   blank=True,
                                   null=True,
                                   help_text='Lay summary should provide a brief overview of project goals and approach. Lay summary may be displayed publicly if the project\'s data gets published in the data catalog')

    dpia = models.TextField(verbose_name='DPIA Link',
                            blank=True,
                            null=True)

    disease_terms = models.ManyToManyField('core.DiseaseTerm',
                                           related_name='projects_w_term',
                                           verbose_name='Disease terms',
                                           blank=True,
                                           help_text='Provide keywords/terms that would characterize the disease that fall in project\'s scope.')

    end_date = models.DateField(verbose_name='End date',
                                blank=True,
                                help_text='Formal end date of project.',
                                null=True)

    erp_notes = models.TextField(verbose_name='Institutional ethics approval notes.',
                                 default='',
                                 help_text='Provide notes on institutional ethics approval. If it does not exist, please state justifications here.',
                                 blank=True,
                                 null=True)

    funding_sources = models.ManyToManyField('core.FundingSource',
                                             blank=True,
                                             related_name='projects_funded',
                                             verbose_name='Funding sources',
                                             help_text='Funding sources are national, international bodies or initiatives that have funded the research project.')

    gene_terms = models.ManyToManyField('core.DiseaseTerm',
                                        verbose_name='List of gene terms',
                                        blank=True,
                                        help_text='Select one or more terms that would characterize the genes that fall in project\'s scope.')

    has_cner = models.BooleanField(default=False,
                                   verbose_name='Has National Ethics Approval?',
                                   help_text='Does the project have an ethics approval from a national body. E.g. In Luxembourg this would be Comité National d\'Ethique de Recherche (CNER)')

    has_erp = models.BooleanField(default=False,
                                  verbose_name='Has Institutional Ethics Approval?',
                                  help_text='Does the project have an ethics approval from an institutional body. E.g. At the LCSB this wuld be the Uni-Luxembourg Ethics Review Panel (ERP)')

    includes_automated_profiling = models.BooleanField(default=False,
                                                       blank=False,
                                                       null=False,
                                                       help_text='An example of profiling in biomedical research is the calculation of disease ratings or scores from clinical attributes.')

    legal_documents = GenericRelation('core.Document', related_query_name='projects')

    umbrella_project = models.ForeignKey('core.Project',
                                         null=True,
                                         blank=True,
                                         verbose_name='Umbrella project',
                                         help_text='If this project is part of a larger project, then please state the umbrella project here.',
                                         on_delete=models.CASCADE, related_name="child_projects")

    phenotype_terms = models.ManyToManyField('core.PhenotypeTerm',
                                             related_name='projects_w_term',
                                             verbose_name='Phenotype terms',
                                             blank=True,
                                             help_text='Select one or more terms that would characterize the phenotypes that fall in project\'s scope.')

    project_web_page = models.URLField(verbose_name='Project''s URL page',
                                       help_text='If the project has a webpage, please provide its URL link here.',
                                       blank=True)

    publications = models.ManyToManyField('core.Publication',
                                          verbose_name='Project''s publications',
                                          blank=True)

    start_date = models.DateField(verbose_name='Start date',
                                  blank=True,
                                  help_text='Formal start date of project.',
                                  null=True)

    study_terms = models.ManyToManyField('core.StudyTerm',
                                         blank=True,
                                         related_name='projects_w_type',
                                         verbose_name='Study features',
                                         help_text='Select one or more features that would characterize the project.')

    title = models.CharField(blank=False,
                             null=True,
                             verbose_name='Title',
                             max_length=500,
                             help_text='Title is the descriptive long project name.')

    local_custodians = models.ManyToManyField('core.User',
                                              related_name='+',
                                              verbose_name='Local custodians',
                                              help_text='Custodians are the local responsibles for the project. This list must include a PI.')

    def __str__(self):
        return self.acronym or self.title or "undefined"


# faster lookup for permissions
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)
