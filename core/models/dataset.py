import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

from core import constants
from .utils import CoreTrackedModel, TextFieldWithInputWidget


class Dataset(CoreTrackedModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = (
            (constants.Permissions.ADMIN.value, 'Responsible of the dataset'),
            (constants.Permissions.EDIT.value, 'Edit the dataset'),
            (constants.Permissions.DELETE.value, 'Delete the dataset'),
            (constants.Permissions.VIEW.value, 'View the dataset'),
            (constants.Permissions.PROTECTED.value, 'View the protected elements'),
        )

    class AppMeta:
        help_text = "Datasets are physical/logical units of data with an associated storage location and access control policy. "


    comments = models.TextField(verbose_name='Other Comments', blank=True, null=True,
                                help_text='Comments should provide any remarks on the dataset such as data\'s purpose.')



    local_custodians = models.ManyToManyField('core.User',
                                              blank=False,
                                              related_name='datasets',
                                              verbose_name='Local custodians',
                                              help_text='Local custodians are the local responsibles for the dataset, this list must include a PI.')

    other_external_id = TextFieldWithInputWidget(blank=True,
                                                 null=True,
                                                 verbose_name='Other Identifiers',
                                                 help_text='If the dataset has other external identifiers such as an Accession Number or a DOI, please list them here.')

    title = TextFieldWithInputWidget(blank=False,
                                     max_length=255,
                                     verbose_name='Title', unique=True,
                                     help_text='Title is a descriptive long name for the dataset.')

    unique_id = models.UUIDField(default=uuid.uuid4,
                                 editable=False,
                                 unique=True,
                                 blank=False,
                                 verbose_name='Unique identifier',
                                 help_text='This is the unique identifier used by DAISY to track this dataset. This field cannot be changed by user.')

    project = models.ForeignKey('core.Project', related_name='datasets', null=True, on_delete=models.SET_NULL,
                                verbose_name='Project of origin',
                                help_text='This is the project that either generated the data in-house or provisioned it from outside.')

    sensitivity = models.ForeignKey(to="core.SensitivityClass", blank=True,
                                    null=True,
                                    on_delete=models.SET_NULL,
                                    verbose_name='Sensitivity class',
                                    help_text='Sensitivity denotes the security classification of this dataset.')

    @property
    def data_types(self):
        all_data_types = set()
        for data_declaration in self.data_declarations.all():
            all_data_types.update(data_declaration.data_types_generated.all())
            all_data_types.update(data_declaration.data_types_received.all())
        return all_data_types


    def collect_contracts(self):
        result = set()
        for share in self.shares.all():
            result.add((share.contract, share))
        for ddec in self.data_declarations.all():
            result.add((ddec.contract,ddec))
        return result

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('dataset', args=[str(self.pk)])

    def get_full_url(self):
        """
        Get the full url of the dataset (with the server scheme and url).
        """
        return '%s://%s%s' % (settings.SERVER_SCHEME, settings.SERVER_URL, self.get_absolute_url())


# faster lookup for permissions
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class DatasetUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Dataset, on_delete=models.CASCADE)


class DatasetGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Dataset, on_delete=models.CASCADE)
