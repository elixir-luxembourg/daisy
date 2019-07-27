from django.db import models
from enumchoicefield import EnumChoiceField, ChoiceEnum
from model_utils.managers import InheritanceManager

from .utils import CoreModel, TextFieldWithInputWidget, classproperty


class StorageLocationCategory(ChoiceEnum):
    master = 'master'
    backup = 'backup'
    copy = 'copy'


class DataLocation(CoreModel):
    """
    Represent a data location.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    # objects = InheritanceManager()

    backend = models.ForeignKey(
        'core.StorageResource',
        verbose_name="Storage back-end",
        on_delete=models.CASCADE
    )

    category = EnumChoiceField(
        StorageLocationCategory, default=StorageLocationCategory.master, blank=False, null=False,
        verbose_name='Nature of data copy.'
    )

    dataset = models.ForeignKey('core.Dataset',
                                related_name='data_locations',
                                on_delete=models.CASCADE
                                )

    datatypes = models.ManyToManyField("core.DataType", verbose_name="Stored datatypes", blank=True,
                                       related_name="storage_locations")

    data_declarations = models.ManyToManyField('core.DataDeclaration',
                                               blank=True,
                                               related_name='data_locations',
                                               verbose_name='Stored data declarations',
                                               help_text='The scope of this storage. Leave empty if all data declarations are stored in a single location.')


    location_description = TextFieldWithInputWidget(blank=True, null=True,
        verbose_name='Location of the data'
    )

    def __str__(self):
        return '{} - {} - {}'.format(self.category, self.backend.name, self.location_description)


