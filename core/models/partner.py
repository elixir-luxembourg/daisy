from django.apps import apps
from django.db import models
from model_utils import Choices
from django_countries.fields import CountryField
from elixir_daisy import settings
from .utils import  CoreTrackedModel, TextFieldWithInputWidget

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




class Partner(CoreTrackedModel):
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



    address = TextFieldWithInputWidget(verbose_name='Address', help_text='The contact address of the partner.')

    country = CountryField(blank_label='select country', blank=True, null=True)

    geo_category = models.CharField(choices=GEO_CATEGORY, blank=False, null=False, default=GEO_CATEGORY.EU,
                                    max_length=20, verbose_name='Geo-Category',
                                    help_text='The  category of the geo-location of partner.')

    sector_category = models.CharField(choices=SECTOR_CATEGORY, blank=False, null=False, default=SECTOR_CATEGORY.PUBLIC,
                                       max_length=20, verbose_name='Sector-Category',
                                       help_text='The  category of the sector that the partner operates in.')

    is_clinical = models.BooleanField(default=False, blank=False, null=False, verbose_name='Is clinical?',
                                      help_text='Please select if this is a clinical partner.')



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
            "pk": self.id.__str__(),
            "name": self.name,
            "elu_accession": self.elu_accession if self.elu_accession else None,
            "acronym": self.acronym if self.acronym else None,
            "is_clinical": self.is_clinical,
            "geo_category": self.geo_category,
            "sector_category": self.sector_category,
            "address": self.address if self.address else None,
            "country_code": self.country.ioc_code if self.country.ioc_code else None
        }
        return base_dict




class HomeOrganisation():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = Partner.objects.get(acronym=settings.COMPANY)
        return cls._instance
