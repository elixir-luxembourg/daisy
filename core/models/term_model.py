import reversion
from enum import Enum
from core.models.utils import CoreModel
from django.db import models


class TermCategory(Enum):
    disease = 'disease'
    study = 'study'
    phenotype = 'phenotype'
    gene = 'gene'

@reversion.register()
class TermModel(CoreModel):
    class Meta:
        abstract = True

    term_id = models.CharField(max_length=200, blank=False)
    label = models.CharField(max_length=300, blank=False)

    def __str__(self):
        return self.label

@reversion.register()
class StudyTerm(TermModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

@reversion.register()
class GeneTerm(TermModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

@reversion.register()
class PhenotypeTerm(TermModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

@reversion.register()
class DiseaseTerm(TermModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
