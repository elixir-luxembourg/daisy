from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

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
                        DataLogType, \
                        Endpoint, \
                        Exposure, \
                        User
from core.forms.endpoint import EndpointEditForm
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


class ContactAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name', 'oidc_id']
    list_display = ('id', 'email', 'first_name', 'last_name', 'oidc_id', 'type')

class DatasetAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ('title', 'project', 'unique_id', 'elu_accession', 'is_published')


class ProjectAdmin(admin.ModelAdmin):
    exclude = ('gene_terms', 'disease_terms', 'phenotype_terms', 'study_terms')
    search_fields = ['acronym', 'title']
    list_display = ('acronym', 'title', 'elu_accession', 'is_published', 'umbrella_project')


# DAISY core models
admin.site.site_header = 'DAISY administration'
admin.site.register(Access)
admin.site.register(Cohort)
admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactType)
admin.site.register(Contract)
admin.site.register(DataDeclaration)
admin.site.register(Dataset, DatasetAdmin)
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
admin.site.register(Project, ProjectAdmin)
admin.site.register(Publication)
admin.site.register(RestrictionClass)
admin.site.register(SensitivityClass)
admin.site.register(Share)
admin.site.register(StorageResource, StorageResourceAdmin)
admin.site.register(UseRestriction)
admin.site.register(DataLogType)

# Term models (term_model.py)
admin.site.register(DiseaseTerm)
admin.site.register(GeneTerm)
admin.site.register(PhenotypeTerm)
admin.site.register(StudyTerm)

# User-related
# See https://docs.djangoproject.com/en/1.8/topics/auth/customizing/#a-full-example
class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'email', 'password', 'source', 'date_joined')

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


user_change_form_fields = (
    'username', 'email', 'password', 'is_active', 
    'source', 'first_name', 'last_name', 'full_name', 
    'is_staff', 'is_superuser', 'groups', 
    'user_permissions', 'date_joined', 'last_login'
)
user_admin_fieldset_row = (None, {'fields': ('username', 'email', 'password', 'is_active', 'source')}, )

if getattr(settings, 'ENABLE_PASSWORD_CHANGE_IN_ADMIN', False):
    user_change_form_fields = user_change_form_fields + ('change_password', )
    user_admin_fieldset_row = (None, {'fields': ('username', 'email', 'password', 'change_password', 'is_active', 'source')}, )


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(help_text='This field contains hashed and salted value')

    
    if getattr(settings, 'ENABLE_PASSWORD_CHANGE_IN_ADMIN', False):
        change_password = forms.CharField(
            label='Set new password:', 
            help_text='Leave empty if no change is needed',
            required=False,
            widget=forms.PasswordInput
        )

    class Meta:
        model = User
        fields = user_change_form_fields

    def clean_password(self):
       # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)

        if getattr(settings, 'ENABLE_PASSWORD_CHANGE_IN_ADMIN', False):
            if len(self.cleaned_data["change_password"]):
                user.set_password(self.cleaned_data["change_password"])

        if commit:
            user.save()

        return user


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm  # Form to change user
    add_form = UserCreationForm  # Form to add new user

    # The fields to be used in displaying the User model in `/admin/core/user/`
    list_display = ('id', 'full_name', 'email', 'source', 'is_staff', 'is_superuser', 'oidc_id')

    # Sections in the Edit page
    fieldsets = (
        user_admin_fieldset_row,
        ('Personal info', {'fields': ('first_name', 'last_name', 'full_name', 'oidc_id')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Additional metdata', {'fields': ('date_joined', 'last_login', 'api_key')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. BaseUserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'last_name', 'first_name', 'email', 'password', 'source', 'date_joined')
            }
        ),
    )

    search_fields = ('full_name', 'email',)
    ordering = ('full_name',)
    filter_horizontal = ()

# User
admin.site.register(User, UserAdmin)


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    form = EndpointEditForm
    list_display = ('name', 'id', 'url_pattern')
    search_fields = ('id', 'name', 'url_pattern')
    ordering = ('id',)


@admin.register(Exposure)
class ExposureAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'id', 'endpoint', 'form_id', 'form_name')
    search_fields = ('id', 'dataset', 'endpoint', 'form_id', 'form_name')
    ordering = ('added',)
