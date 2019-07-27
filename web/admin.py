from django import forms
from django.contrib import admin

from core.models import Contract, Contact, ContactType, Dataset, DataType, Document, DocumentType, FundingSource, \
    Partner, Project, DataDeclaration, Cohort, Publication, RestrictionClass, UseRestriction, Share, StorageResource, User
from core.models.storage_location import DataLocation

# Register your models here.

admin.site.register(Contract)
admin.site.register(Contact)
admin.site.register(Cohort)
admin.site.register(ContactType)
admin.site.register(DataDeclaration)
admin.site.register(Dataset)
admin.site.register(DataType)
admin.site.register(Document)
admin.site.register(DocumentType)
admin.site.register(FundingSource)
admin.site.register(Partner)
admin.site.register(Project)
admin.site.register(Publication)
admin.site.register(RestrictionClass)
admin.site.register(UseRestriction)
admin.site.register(Share)
admin.site.register(User)


class StorageResourceForm(forms.ModelForm):
    class Meta:
        model = StorageResource
        fields = ['name', 'slug', 'description', 'managed_by']



class StorageResourceAdmin(admin.ModelAdmin):
    form = StorageResourceForm


admin.site.register(StorageResource, StorageResourceAdmin)
