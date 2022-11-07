import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase
from core import constants
from core.permissions.mapping import PERMISSION_MAPPING

from .utils import CoreTrackedModel, TextFieldWithInputWidget
from .partner import HomeOrganisation


class Dataset(CoreTrackedModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = PERMISSION_MAPPING["Dataset"]  # Adds PROTECTED and ADMIN permissions to Dataset

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
            if share.contract is not None:
                result.add((share.contract, share))
        for ddec in self.data_declarations.all():
            if ddec.contract is not None:
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



    def to_dict(self):
        contact_dicts = []

        # p = HomeOrganisation()

        for lc in self.local_custodians.all():
            contact_dicts.append({
                "first_name": lc.first_name,
                 "last_name": lc.last_name,
                 "email": lc.email,
                 "role":  "Principal_Investigator" if lc.is_part_of(constants.Groups.VIP.name) else "Researcher",
                 "affiliations": [HomeOrganisation().name]
            })

        storage_dicts = []
        for dl in self.data_locations.all():
            storage_dicts.append({
                "platform": dl.backend.name,
                "location": dl.location_description,
                "accesses": [ acc.access_notes for acc in dl.accesses.all()]
            })

        transfer_dicts = []
        for trf in self.shares.all():
            transfer_dicts.append({
                "partner": trf.partner.name,
                 "transfer_details": trf.share_notes,
                 "transfer_date":  trf.granted_on.strftime('%Y-%m-%d') if trf.granted_on else None
            })

        base_dict = {
            "source": settings.SERVER_URL,
            "id_at_source": self.id.__str__(),
            "external_id": self.elu_accession,
            "name": self.title,
            "description":  self.comments if self.comments else None,
            "elu_uuid": self.unique_id.__str__() if self.unique_id else None,
            "other_external_id": self.other_external_id if self.other_external_id else None,
            "project": self.project.acronym if self.project else None,
            "project_external_id": self.project.elu_accession if self.project else None,
            "data_declarations": [ddec.to_dict() for ddec in self.data_declarations.all()],
            "legal_bases": [x.to_dict() for x in self.legal_basis_definitions.all()],
            "storages": storage_dicts,
            "transfers": transfer_dicts,
            "contacts": contact_dicts,
            "metadata": self.scientific_metadata
        }
        return base_dict

    def serialize_to_export(self):
        import functools
        d = self.to_dict()

        contacts = map(lambda v: f"[{v['first_name']} {v['last_name']}, {v['email']}]", d['contacts'])
        d['contacts'] = ','.join(contacts)

        transfers = map(lambda v: f"[{v['partner']} {v['transfer_details']}, {v['transfer_date']}]", d['transfers'])
        d['transfers'] = ','.join(transfers)

        storages = map(lambda v: f"[{v['platform']} {v['location']}]", d['storages'])
        d['storages'] = ','.join(storages)
        
        data_declarations = map(lambda v: f"[{v['title']}]", d['data_declarations'])
        d['data_declarations'] = ','.join(data_declarations)

        legal_bases = map(lambda v: f"[{v['platform']} {v['location']}]", d['storages'])
        d['legal_bases'] = legal_bases
        return d

    def publish(self, save=True):
        if self.project:
            self.project.publish()
        
        for data_declaration in self.data_declarations.all():
            data_declaration.publish_subentities()

        super().publish()
        

# faster lookup for permissions
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class DatasetUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Dataset, on_delete=models.CASCADE)


class DatasetGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Dataset, on_delete=models.CASCADE)
