import json
import os

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from guardian.shortcuts import assign_perm
from ontobio import obograph_util, Ontology
from django.db import connection
from core.exceptions import FixtureImportError
from core.models import ContactType, DataType, DocumentType, StorageResource, FundingSource, RestrictionClass, \
    SensitivityClass, Cohort, Contact, GDPRRole, LegalBasisType, PersonalDataType
from core.models.partner import Partner
from core.models.term_model import GeneTerm, StudyTerm, DiseaseTerm, PhenotypeTerm
from core.permissions import PERMISSION_MAPPING

FIXTURE_DIR = os.path.join(settings.BASE_DIR, 'core', 'fixtures')


def get_classes(ontology):
    result = []
    for n_id in ontology.nodes():
        n_dict = ontology.node(n_id)
        if 'type' in n_dict:
            if ontology.node_type(n_id) == 'CLASS':
                label = ontology.label(n_id)
                if label:
                    result.append((n_id, label))
    return result


class Command(BaseCommand):
    help = 'load initial data into database'

    @staticmethod
    def create_gdpr_roles():
        print('Creating GDPR roles')
        GDPRRole.objects.all().delete()
        with open(os.path.join(FIXTURE_DIR, 'gdpr-roles.json'), 'r') as handler:
            data = json.load(handler)
            for gdpr_role in data:
                GDPRRole.objects.get_or_create(
                    **gdpr_role)


    @staticmethod
    def create_contact_types():
        print('Creating contact types')
        ContactType.objects.all().delete()
        with open(os.path.join(FIXTURE_DIR, 'contact-types.json'), 'r') as handler:
            data = json.load(handler)
            for contact_type in data:
                ContactType.objects.get_or_create(
                    **contact_type
                )

    @staticmethod
    def create_datatypes():
        print('Creating datatypes')
        DataType.objects.all().delete()

        with open(os.path.join(FIXTURE_DIR, 'datatypes.json'), 'r') as handler:
            data = json.load(handler)
            for data_type in data:
                DataType.objects.get_or_create(
                    **data_type
                )


    @staticmethod
    def create_document_types():
        print('Creating document types')

        DocumentType.objects.all().delete()
        with open(os.path.join(FIXTURE_DIR, 'document-types.json'), 'r') as handler:
            data = json.load(handler)
            for document_types in data:
                DocumentType.objects.get_or_create(
                    **document_types
                )

    @staticmethod
    def create_funding_sources():
        print('Creating funding sources')

        FundingSource.objects.all().delete()
        with open(os.path.join(FIXTURE_DIR, 'funding-sources.json'), 'r') as handler:
            data = json.load(handler)
            for funding_source in data:
                FundingSource.objects.get_or_create(
                    **funding_source
                )


    @staticmethod
    def create_sensitivity_classes():
        print('Creating sensitivity classes')
        with open(os.path.join(FIXTURE_DIR, 'sensitivity-class.json'), 'r') as handler:
            data = json.load(handler)
            for sensitivity_class in data:
                SensitivityClass.objects.get_or_create(
                    **sensitivity_class
                )

    @staticmethod
    def create_restriction_classes():
        print('Creating restriction classes')
        with open(os.path.join(FIXTURE_DIR, 'restriction-class.json'), 'r') as handler:
            data = json.load(handler)
            for restriction_class in data:
                RestrictionClass.objects.get_or_create(
                    **restriction_class
                )

    @staticmethod
    def create_storage_resources():
        print('Creating storage resources')
        with open(os.path.join(FIXTURE_DIR, 'storage-resource.json'), 'r') as handler:
            data = json.load(handler)
            for storage_resource in data:
                StorageResource.objects.get_or_create(
                    **storage_resource
                )

    @staticmethod
    def create_roles_and_permissions():
        # assign permissions to groups
        print('Creating roles and permissions')
        for group_enum, permission_mapping in PERMISSION_MAPPING.items():
            group, _ = Group.objects.get_or_create(name=group_enum.value)
            group.permissions.clear()
            for klassname, permissions in permission_mapping.items():
                model = apps.get_model(klassname)
                content_type = ContentType.objects.get_for_model(model)
                for perm in permissions:
                    permission_object = Permission.objects.get(
                        content_type=content_type,
                        codename=perm.value,
                    )
                    assign_perm(permission_object, group)

    @staticmethod
    def create_elu_institutions():
        print('Creating institutions')
        with open(os.path.join(FIXTURE_DIR, 'elu-institutions.json'), 'r', encoding='utf-8') as handler:
            data = json.load(handler)
            for partner in data:
                _current = {k: v for k, v in partner.items()}
                _current.update({'is_published': True})
                try:
                    p = Partner.objects.get(elu_accession=_current['elu_accession'])
                    Partner.objects.filter(pk=p.pk).update(**_current)
                except Partner.DoesNotExist:
                    Partner.objects.create(**_current)

    @staticmethod
    def create_elu_cohorts():
        print('Creating cohorts')
        with open(os.path.join(FIXTURE_DIR, 'elu-cohorts.json'), 'r', encoding='utf-8') as handler:
            data = json.load(handler)
            for cohort in data:
                try:
                    c = Cohort.objects.get(elu_accession=cohort['elu_accession'])
                except Cohort.DoesNotExist:
                    c = Cohort.objects.create(elu_accession=cohort['elu_accession'])
                c.title = cohort['title']
                c.comments = cohort.get('title', None)
                if 'institutes' in cohort:
                    institutes = []
                    for ins in cohort['institutes']:
                        try:
                            i = Partner.objects.get(elu_accession=ins)
                            institutes.append(i)
                        except Partner.DoesNotExist:
                            raise FixtureImportError(data="unknown partner institute {}".format(ins))
                    c.institutes.set(institutes)
                if 'owners' in cohort:
                    owners = []
                    for omb in cohort['owners']:
                        contact_type_pi, _ = ContactType.objects.get_or_create(name="Principal_Investigator")

                        omb_name = omb.split()

                        first_name = omb_name[0]
                        last_name = " ".join(omb_name[1:])
                        contact, _ = Contact.objects.get_or_create(
                            first_name=first_name,
                            last_name=last_name,
                            type=contact_type_pi
                        )
                        owners.append(contact)
                    c.owners.set(owners)
                c.save()

    @staticmethod
    def create_study_terms():
        print('Removing existing study terms')
        with connection.cursor() as cursor:
            cursor.execute("truncate core_studyterm cascade")
        print('Creating study terms')
        handle = os.path.join(FIXTURE_DIR, 'edda.json')
        with open(handle, 'r', encoding='utf-8') as f:
            edda_json = f.read()
            g = obograph_util.convert_json_object(json.loads(edda_json))
            ont = Ontology(handle=handle, payload=g)
            study_terms = []
            for class_node in get_classes(ont):
                study_terms.append(StudyTerm(term_id=class_node[0], label=class_node[1]))
            StudyTerm.objects.bulk_create(study_terms)

    @staticmethod
    def create_disease_terms():
        print('Removing existing disease terms')
        with connection.cursor() as cursor:
            cursor.execute("truncate core_diseaseterm cascade")
        print('Creating hdo disease terms')
        handle = os.path.join(FIXTURE_DIR, 'hdo.json')
        with open(handle, 'r', encoding='utf-8') as f:
            hdo_json = f.read()
            g = obograph_util.convert_json_object(json.loads(hdo_json))
            ont = Ontology(handle=handle, payload=g)
            disease_terms = []
            for class_node in get_classes(ont):
                disease_terms.append(DiseaseTerm(term_id=class_node[0], label=class_node[1]))
            DiseaseTerm.objects.bulk_create(disease_terms)

    @staticmethod
    def create_phenotype_terms():
        print('Removing existing phenotype terms')
        with connection.cursor() as cursor:
            cursor.execute("truncate core_phenotypeterm cascade")
        print('Creating hpo phenotype terms')
        handle = os.path.join(FIXTURE_DIR, 'hpo.json')
        with open(handle, 'r', encoding='utf-8') as f:
            hpo_json = f.read()
            g = obograph_util.convert_json_object(json.loads(hpo_json))
            ont = Ontology(handle=handle, payload=g)
            phenotype_terms = []
            for class_node in get_classes(ont):
                phenotype_terms.append(PhenotypeTerm(term_id=class_node[0], label=class_node[1]))
            PhenotypeTerm.objects.bulk_create(phenotype_terms)

    @staticmethod
    def create_gene_terms():
        print('Removing existing gene terms')
        with connection.cursor() as cursor:
            cursor.execute("truncate core_geneterm cascade")
        print('Importing hgnc gene terms')
        handle = os.path.join(FIXTURE_DIR, 'hgnc.json')
        with open(handle, 'r', encoding='utf-8') as f:
            hgnc_json = f.read()
            g = obograph_util.convert_json_object(json.loads(hgnc_json))
            ont = Ontology(handle=handle, payload=g)
            gene_terms = []
            for n_id in ont.nodes():
                n_dict = ont.node(n_id)
                if 'type' in n_dict:
                    if ont.node_type(n_id) == 'CLASS':
                        for t in n_dict['meta']['basicPropertyValues']:
                            if t['pred'] == 'http://ncicb.nci.nih.gov/xml/owl/EVS/Hugo.owl#Approved_Symbol':
                                symbol = t['val']
                                if not symbol.endswith('~withdrawn'):
                                    # print('{}   {}'.format(n_id, symbol))
                                    gene_terms.append(GeneTerm(term_id=n_id, label=symbol))
                                    break
            GeneTerm.objects.bulk_create(gene_terms)


    @staticmethod
    def create_legal_basis_types():
        print('Creating GDPR-defined categories of legal basis.')
        with open(os.path.join(FIXTURE_DIR, 'legal-basis-types.json'), 'r', encoding='utf-8') as handler:
            data = json.load(handler)
            for lbt in data:
                LegalBasisType.objects.get_or_create(
                    **lbt
                )

    @staticmethod
    def create_personal_data_types():
        print('Creating GDPR-defined categories personal data.')
        with open(os.path.join(FIXTURE_DIR, 'personal-data-types.json'), 'r', encoding='utf-8') as handler:
            data = json.load(handler)
            for lbt in data:
                PersonalDataType.objects.get_or_create(
                    **lbt
                )

    def handle(self, *args, **options):
        self.create_study_terms()
        self.create_disease_terms()
        self.create_phenotype_terms()
        self.create_gene_terms()
        self.create_contact_types()
        self.create_datatypes()
        self.create_sensitivity_classes()
        self.create_legal_basis_types()
        self.create_personal_data_types()
        self.create_restriction_classes()
        self.create_document_types()
        self.create_funding_sources()
        self.create_storage_resources()
        self.create_roles_and_permissions()
        self.create_elu_institutions()
        self.create_elu_cohorts()
        self.create_gdpr_roles()
        print('done')
