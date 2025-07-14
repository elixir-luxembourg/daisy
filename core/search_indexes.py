from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from core.models import (
    Dataset,
    Contract,
    Project,
    DataDeclaration,
    Cohort,
    Contact,
    Partner,
    GDPRRole,
)


class DataDeclarationIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return DataDeclaration

    def get_updated_field(self):
        return "updated"

    text = indexes.CharField(document=True, use_template=True)
    pk = indexes.IntegerField(indexed=True, stored=True, faceted=True)
    cohorts = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    consent_status = indexes.CharField(
        model_attr="consent_status", indexed=True, stored=True, faceted=True
    )
    data_types = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    data_types_generated = indexes.MultiValueField(
        indexed=True, stored=True, faceted=True
    )
    data_types_received = indexes.MultiValueField(
        indexed=True, stored=True, faceted=True
    )
    deidentification_method = indexes.CharField(indexed=True, stored=True, faceted=True)
    embargo_date = indexes.DateField(indexed=True, stored=True)
    end_of_storage_duration = indexes.DateField(indexed=True, stored=True)
    has_special_subjects = indexes.BooleanField(indexed=True, stored=True, faceted=True)
    local_custodians = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    other_external_id = indexes.CharField(indexed=True, stored=True, faceted=True)
    project = indexes.CharField(indexed=True, stored=True, faceted=True)
    special_subjects_description = indexes.CharField(
        indexed=True, stored=True, faceted=True
    )
    subjects_category = indexes.CharField(indexed=True, stored=True, faceted=True)
    submission_id = indexes.CharField(indexed=True, stored=True, faceted=True)
    title = indexes.CharField(indexed=True, stored=True, faceted=True)
    title_l = indexes.CharField(indexed=False, stored=True)
    unique_id = indexes.CharField(indexed=True, stored=True, faceted=True)
    autocomplete = indexes.EdgeNgramField()

    def prepare_autocomplete(self, obj):
        text_parts = [
            obj.title,
            str(obj.dataset),
            " ".join([str(c for c in obj.cohorts.all())]),
            " ".join([str(l) for l in obj.dataset.local_custodians.all()]),
        ]
        if obj.dataset.project:
            text_parts.append(str(obj.dataset.project))
        return " ".join(text_parts)

    def prepare_title(self, obj):
        return obj.title

    def prepare_title_l(self, obj):
        if obj.title:
            return obj.title.lower().strip()

    def prepare_deidentification_method(self, obj):
        return obj.deidentification_method.name

    def prepare_data_use_conditions(self, obj):
        return [o.condition_class for o in obj.data_use_conditions.all()]

    def prepare_subjects_category(self, obj):
        return obj.subjects_category.name

    def prepare_cohorts(self, obj):
        return [str(c) for c in obj.cohorts.all()]

    def prepare_project(self, obj):
        if obj.dataset.project:
            return str(obj.dataset.project)
        return None

    def prepare_local_custodians(self, obj):
        return [u.full_name for u in obj.dataset.local_custodians.all()]


class CohortIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Cohort

    def get_updated_field(self):
        return "updated"

    text = indexes.CharField(document=True, use_template=True)
    pk = indexes.IntegerField(indexed=True, stored=True, faceted=True)
    owners = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    title = indexes.CharField(indexed=True, stored=True, faceted=True)
    title_l = indexes.CharField(indexed=False, stored=True)
    institutes = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    ethics_confirmation = indexes.BooleanField(indexed=True, stored=True, faceted=False)

    def prepare_title(self, obj):
        return obj.title

    def prepare_title_l(self, obj):
        if obj.title:
            return obj.title.lower().strip()

    def prepare_owners(self, obj):
        return [str(i) for i in obj.owners.all()]

    def prepare_institutes(self, obj):
        return [str(i) for i in obj.institutes.all()]

    def prepare_ethics_confirmation(self, obj):
        return obj.ethics_confirmation


class DatasetIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Dataset

    # needed
    text = indexes.CharField(document=True, use_template=True)

    pk = indexes.IntegerField(indexed=True, stored=True, faceted=True)

    data_types = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    is_published = indexes.BooleanField(indexed=True, stored=True, faceted=True)

    local_custodians = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    other_external_id = indexes.CharField(indexed=True, stored=True, faceted=True)

    project = indexes.CharField(indexed=True, stored=True, faceted=True)

    title = indexes.CharField(indexed=True, stored=True, faceted=True)
    title_l = indexes.CharField(indexed=False, stored=True)

    unique_id = indexes.CharField(indexed=True, stored=True, faceted=True)

    def prepare_title(self, obj):
        return obj.title

    def prepare_title_l(self, obj):
        if obj.title:
            return obj.title.lower().strip()

    def prepare_is_published(self, obj):
        return obj.is_published

    def prepare_project(self, obj):
        if obj.project:
            return str(obj.project)
        else:
            return ""

    def prepare_data_types(self, obj):
        return [d.name for d in obj.data_types]

    def prepare_local_custodians(self, obj):
        return [u.full_name for u in obj.local_custodians.all()]

    def get_updated_field(self):
        return "updated"


class ContractIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Contract

    def get_updated_field(self):
        return "updated"

    # needed
    text = indexes.CharField(document=True, use_template=True)

    pk = indexes.IntegerField(indexed=True, stored=True, faceted=True)

    local_custodians = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    contacts = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    partners = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    has_legal_documents = indexes.BooleanField(indexed=True, stored=True, faceted=True)

    partners_roles = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    project = indexes.CharField(indexed=True, stored=True, faceted=True)

    data_declarations = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    def prepare_local_custodians(self, obj):
        return [u.full_name for u in obj.local_custodians.all()]

    def prepare_partners_roles(self, obj):
        roles = GDPRRole.objects.filter(partners_roles__contract=obj).distinct()
        return [str(r) for r in roles]

    def prepare_contacts(self, obj):
        contacts = []
        for p in obj.partners_roles.all():
            for c in p.contacts.all():
                contacts.append("%s %s" % (c.first_name, c.last_name))
        if contacts:
            return contacts
        else:
            return ["no collaborator"]

    def prepare_partners(self, obj):
        return [p.partner.name for p in obj.partners_roles.all()]

    def prepare_has_legal_documents(self, obj):
        return obj.legal_documents.exists()

    def prepare_project(self, obj):
        try:
            acronym = obj.project
            return acronym
        except AttributeError:
            return None

    def prepare_data_declarations(self, obj):
        return [
            data_declaration.title for data_declaration in obj.data_declarations.all()
        ]


class PartnerIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Partner

    def get_updated_field(self):
        return "updated"

    text = indexes.CharField(document=True, use_template=True)
    acronym = indexes.CharField(indexed=True, stored=True)
    acronym_l = indexes.CharField(indexed=False, stored=True)
    address = indexes.CharField(indexed=True, stored=True)
    address_l = indexes.CharField(indexed=False, stored=True)
    name = indexes.CharField(indexed=True, stored=True)
    name_l = indexes.CharField(indexed=False, stored=True)
    is_clinical = indexes.BooleanField(indexed=True, stored=True, faceted=True)
    geo_category = indexes.CharField(indexed=True, stored=True, faceted=True)
    sector_category = indexes.CharField(indexed=True, stored=True, faceted=True)

    def prepare_name(self, obj):
        return obj.name

    def prepare_name_l(self, obj):
        if obj.name:
            return obj.name.lower().strip()

    def prepare_acronym(self, obj):
        return obj.acronym

    def prepare_acronym_l(self, obj):
        if obj.acronym:
            return obj.acronym.lower().strip()

    def prepare_address(self, obj):
        return obj.address

    def prepare_address_l(self, obj):
        if obj.address:
            return obj.address.lower().strip()

    def prepare_geo_category(self, obj):
        return obj.geo_category_display

    def prepare_sector_category(self, obj):
        return obj.sector_category_display

    def prepare_is_clinical(self, obj):
        return obj.is_clinical


class ContactIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Contact

    def get_updated_field(self):
        return "updated"

    # needed
    text = indexes.CharField(document=True, use_template=True)

    first_name = indexes.CharField(indexed=True, stored=True)
    last_name = indexes.CharField(indexed=True, stored=True)

    first_name_l = indexes.CharField(indexed=False, stored=True)
    last_name_l = indexes.CharField(indexed=False, stored=True)

    partners = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    type = indexes.CharField(indexed=False, stored=True, faceted=True)

    def prepare_first_name(self, obj):
        return obj.first_name

    def prepare_first_name_l(self, obj):
        if obj.first_name:
            return obj.first_name.lower().strip()

    def prepare_last_name(self, obj):
        return obj.last_name

    def prepare_last_name_l(self, obj):
        if obj.last_name:
            return obj.last_name.lower().strip()

    def prepare_type(self, obj):
        return obj.type

    def prepare_partners(self, obj):
        return [p.name for p in obj.partners.all()]


class ProjectIndex(CelerySearchIndex, indexes.Indexable):
    def get_model(self):
        return Project

    def get_updated_field(self):
        return "updated"

    # needed
    text = indexes.CharField(document=True, use_template=True)
    acronym = indexes.CharField(indexed=True, stored=True, faceted=True)
    acronym_l = indexes.CharField(indexed=False, stored=True)
    cner_notes = indexes.CharField(indexed=True, stored=True)
    contacts = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    company_personnel = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    description = indexes.CharField(indexed=True, stored=True, faceted=True)
    disease_terms = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    end_year = indexes.IntegerField(indexed=True, stored=True, faceted=True)
    erp_notes = indexes.CharField(indexed=True, stored=True, faceted=True)
    funding_sources = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    gene_terms = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    has_cner = indexes.BooleanField(indexed=True, stored=True, faceted=True)
    has_erp = indexes.BooleanField(indexed=True, stored=True, faceted=True)
    has_legal_documents = indexes.BooleanField(indexed=True, stored=True, faceted=True)
    umbrella_project = indexes.CharField(indexed=True, stored=True, faceted=True)
    phenotype_terms = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    project_web_page = indexes.CharField(indexed=True, stored=True, faceted=True)
    publications = indexes.MultiValueField(indexed=True, stored=True)
    start_date = indexes.DateField(indexed=True, stored=True)
    start_year = indexes.IntegerField(indexed=True, stored=True, faceted=True)
    study_terms = indexes.MultiValueField(indexed=True, stored=True, faceted=True)
    title = indexes.CharField(indexed=True, stored=True, faceted=True)
    title_l = indexes.CharField(indexed=False, stored=True)
    local_custodians = indexes.MultiValueField(indexed=True, stored=True, faceted=True)

    def prepare_acronym_l(self, obj):
        if obj.acronym:
            return obj.acronym.lower().strip()

    def prepare_title_l(self, obj):
        if obj.title:
            return obj.title.lower().strip()

    def prepare_contacts(self, obj):
        return [str(o) for o in obj.contacts.all()]

    def prepare_company_personnel(self, obj):
        return [str(o) for o in obj.company_personnel.all()]

    def prepare_funding_sources(self, obj):
        return [str(o) for o in obj.funding_sources.all()]

    def prepare_publications(self, obj):
        return [str(o) for o in obj.publications.all()]

    def prepare_local_custodians(self, obj):
        return [str(o) for o in obj.local_custodians.all()]

    def prepare_has_legal_documents(self, obj):
        return obj.legal_documents.exists()

    def prepare_acronym(self, obj):
        return obj.acronym

    def prepare_cner_notes(self, obj):
        return obj.cner_notes

    def prepare_description(self, obj):
        return obj.description

    def prepare_disease_terms(self, obj):
        return [str(o) for o in obj.disease_terms.all()]

    def prepare_end_year(self, obj):
        if obj.end_date:
            return obj.end_date.year
        else:
            return None

    def prepare_erp_notes(self, obj):
        return obj.erp_notes

    def prepare_gene_terms(self, obj):
        return [str(o) for o in obj.gene_terms.all()]

    def prepare_has_cner(self, obj):
        return obj.has_cner

    def prepare_has_erp(self, obj):
        return obj.has_erp

    def prepare_umbrella_project(self, obj):
        return obj.umbrella_project

    def prepare_phenotype_terms(self, obj):
        return [str(o) for o in obj.phenotype_terms.all()]

    def prepare_project_web_page(self, obj):
        return obj.project_web_page

    def prepare_start_year(self, obj):
        if obj.start_date:
            return obj.start_date.year
        else:
            return None

    def prepare_start_date(self, obj):
        if obj.start_date:
            return obj.start_date
        else:
            return None

    def prepare_study_terms(self, obj):
        return [str(o) for o in obj.study_terms.all()]

    def prepare_title(self, obj):
        return obj.title
