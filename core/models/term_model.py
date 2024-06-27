from enum import Enum
from core.models.utils import CoreModel
from django.db import models


class TermCategory(Enum):
    disease = "disease"
    study = "study"
    phenotype = "phenotype"
    gene = "gene"


class TermModel(CoreModel):
    class Meta:
        abstract = True

    term_id = models.CharField(max_length=200, blank=False)
    label = models.CharField(max_length=300, blank=False)

    def __str__(self):
        return self.label


class StudyTerm(TermModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]


class GeneTerm(TermModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]


class PhenotypeTerm(TermModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]


class DiseaseTerm(TermModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
