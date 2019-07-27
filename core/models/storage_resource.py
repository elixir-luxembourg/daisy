from django.db import models

from .utils import CoreModel, TextFieldWithInputWidget
from core.models.storage_location import DataLocation

class StorageResource(CoreModel):
    """
    Represents storage Back-end, like Aspera, HPC, ownCloud etc.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['name']

    name = TextFieldWithInputWidget(
        max_length=128,
        verbose_name="Name", unique=True
    )

    slug = models.SlugField(
        max_length=128,
        verbose_name="Slug", unique=True
    )

    description = models.TextField(
        verbose_name='Description',
        blank=True
    )

    managed_by = models.TextField(
        verbose_name='Managed by',
    )

    # location_definition = models.TextField()

    acl_policy_description = TextFieldWithInputWidget(max_length=255, blank=True, null=True,
                                                      verbose_name='Default Access Control Policy of platform')

    # def get_location_class(self):
    #     """
    #     Get the mapped location definition for the storage resource.
    #     """
    #     return DataLocation.SUBCLASS(self.location_definition)


    def __str__(self):
        return "{}".format(self.name)
