from django import forms
from django.contrib import admin

from core.models import Access, \
                        Cohort, \
                        ContactType, \
                        Contact, \
                        Document, \
                        DocumentType, \
                        FundingSource, \
                        GDPRRole, \
                        LegalBasis, \
                        Contract, \
                        DataDeclaration, \
                        Dataset, \
                        DataType, \
                        LegalBasisType, \
                        Partner, \
                        PersonalDataType, \
                        Project, \
                        Publication, \
                        RestrictionClass, \
                        SensitivityClass, \
                        Share, \
                        StorageResource, \
                        UseRestriction, \
                        User
from core.models.contract import PartnerRole
from core.models.storage_location import DataLocation
from core.models.term_model import DiseaseTerm, \
                                   GeneTerm, \
                                   PhenotypeTerm, \
                                   StudyTerm


class StorageResourceForm(forms.ModelForm):
    class Meta:
        model = StorageResource
        fields = ['name', 'slug', 'description', 'managed_by']


class StorageResourceAdmin(admin.ModelAdmin):
    form = StorageResourceForm

admin.site.site_header = 'DAISY administration'
admin.site.register(Access)
admin.site.register(Cohort)
admin.site.register(Contact)
admin.site.register(ContactType)
admin.site.register(Contract)
admin.site.register(DataDeclaration)
admin.site.register(Dataset)
admin.site.register(DataLocation)  # storage_location.py
admin.site.register(DataType)
admin.site.register(DocumentType)
admin.site.register(Document)
admin.site.register(FundingSource)
admin.site.register(GDPRRole)
admin.site.register(LegalBasis)
admin.site.register(LegalBasisType)
admin.site.register(Partner)
admin.site.register(PartnerRole)  # contract.py
admin.site.register(PersonalDataType)
admin.site.register(Project)
admin.site.register(Publication)
admin.site.register(RestrictionClass)
admin.site.register(SensitivityClass)
admin.site.register(Share)
admin.site.register(StorageResource, StorageResourceAdmin)
admin.site.register(UseRestriction)
admin.site.register(User)

# Term models (term_model.py)
admin.site.register(DiseaseTerm)
admin.site.register(GeneTerm)
admin.site.register(PhenotypeTerm)
admin.site.register(StudyTerm)
