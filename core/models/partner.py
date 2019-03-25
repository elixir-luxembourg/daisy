from django.apps import apps
from django.db import models
from model_utils import Choices

from .utils import COMPANY, CoreModel, TextFieldWithInputWidget

GEO_CATEGORY = Choices(
    ('EU', 'EU'),
    ('Non_EU', 'Non-EU'),
    ('International', 'International'),
    ('National', 'National')
)

SECTOR_CATEGORY = Choices(
    ('PUBLIC', 'Public'),
    ('PRIVATE_NP', 'Private Non-Profit'),
    ('PRIVATE_P', 'Private For-Profit')
)


class Partner(CoreModel):
    """
    Represents a partner.
      {
        "elu_accession": "ELU_I_6",
        "name": "University Hospital of the Saarland",
        "geo_category": "EU",
        "sector_category": "PUBLIC",
        "is_clinical": true,
        "acronym": "UKS Homburg"
    },
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['name']

    class AppMeta:
        help_text = "Partners are collaborators which are the source and/or recipient of data. " \
                    "Partners are also legal entities with which contracts are signed. " \
                    "Clinics, research institutes, or data hubs are examples of Partners."


    acronym = TextFieldWithInputWidget(
        max_length=255,
        verbose_name='Acronym',
        help_text='The acronym for the partner institutes name e.g. EMBL for European Molecular Biology Laboratory.'
    )

    elu_accession = models.CharField(default='-', blank=False, null=False, max_length=20)

    address = TextFieldWithInputWidget(verbose_name='Address', help_text='The contact address of the partner.')

    geo_category = models.CharField(choices=GEO_CATEGORY, blank=False, null=False, default=GEO_CATEGORY.EU,
                                    max_length=20, verbose_name='Geo-Category',
                                    help_text='The  category of the geo-location of partner.')

    sector_category = models.CharField(choices=SECTOR_CATEGORY, blank=False, null=False, default=SECTOR_CATEGORY.PUBLIC,
                                       max_length=20, verbose_name='Sector-Category',
                                       help_text='The  category of the sector that the partner operates in.')

    is_clinical = models.BooleanField(default=False, blank=False, null=False, verbose_name='Is clinical?',
                                      help_text='Please select if this is a clinical partner.')

    is_published = models.BooleanField(default=False, blank=False, null=False, verbose_name='Is published?',
                                       help_text='Please select if ELU_Accession is present ')

    name = TextFieldWithInputWidget(
        blank=False,
        null=False,
        verbose_name='Name',
        help_text='The name of the partner institute.',
        unique=True
    )


    @property
    def contracts(self):
        # retrieve model dynamically to prevent circular dependencies
        contract_model = apps.get_model('core', 'Contract')
        return contract_model.objects.filter(partners_roles__partner=self)


    def __str__(self):
        return self.name


    @property
    def geo_category_display(self):
        return GEO_CATEGORY[self.geo_category]


    @property
    def sector_category_display(self):
        return SECTOR_CATEGORY[self.sector_category]


    def to_dict(self):
        base_dict = {
            'elu_accession': self.elu_accession,
            'name': self.name,
            'acronym': self.acronym
        }
        return base_dict
