import os
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from model_utils import Choices
from .utils import CoreModel
from core import constants


def get_file_name(instance, filename):
    """
    Return the path of the final path of the document on the filsystem.
    """
    now = timezone.now().strftime('%Y/%m/%d')
    return f'documents/{instance.content_type.name}/{now}/{instance.object_id}_{filename}'


class Document(CoreModel):
    """
    Represents a document
    """

    type = Choices(("not_specified", "Not Specified"),
                   ("agreement", "Agreement"),
                   ("ethics_approval", "Ethics Approval"),
                   ("consent_form", "Consent Form"),
                   ("subject_information_sheet", "Subject Information Sheet"),
                   ("project_proposal", "Project Proposal"),
                   ('data_protection_impact_assessment', 'Data Protection Impact Assessment'),
                   ("other", "Other"))

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = (
            (constants.Permissions.PROTECTED.value, 'Protected document'),
        )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    content = models.FileField(upload_to=get_file_name)
    content_url = models.URLField(verbose_name='Document Url', null=True, blank=True)
    content_notes = models.TextField(verbose_name='Document Notes',
                                     blank=True,
                                     null=True)
    domain_type = models.TextField(verbose_name='Domain Type', choices=type, default=type.not_specified)

    expiry_date = models.DateField(verbose_name='Expiry date',
                                blank=True,
                                help_text='If the document has a validity period, please specify the expiry date here.',
                                null=True)

    def __str__(self):
        return f"{self.content.name} ({self.content_object})"

    @property
    def shortname(self):
        """
        Return the name of the files without the path relative to MEDIA_ROOT.
        Also remove the id prefix of the document.
        """
        return  ''.join(os.path.basename(self.content.path).split('_')[1:])

    @property
    def size(self):
        return self.content.size

@receiver(post_delete, sender=Document, dispatch_uid='document_delete')
def document_cleanup(sender, instance, **kwargs):
    if hasattr(instance.content, 'path') and os.path.exists(instance.content.path):
        default_storage.delete(instance.content.path)
