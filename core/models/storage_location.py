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


    # @classproperty
    # @classmethod
    # def SUBCLASS_OBJECT_CHOICES(cls):
    #     "All known subclasses, keyed by a unique name per class."
    #     return {rel.name: rel.related_model for rel in cls._meta.related_objects if rel.parent_link}
    #
    # @classproperty
    # @classmethod
    # def SUBCLASS_CHOICES(cls):
    #     "Available subclass choices, with nice names."
    #     return [
    #         (name, model._meta.verbose_name)
    #         for name, model in cls.SUBCLASS_OBJECT_CHOICES.items()
    #     ]
    #
    # @classmethod
    # def SUBCLASS(cls, name):
    #     "Given a subclass name, return the subclass."
    #     return cls.SUBCLASS_OBJECT_CHOICES.get(name, cls)
    #
    # def cast(self):
    #     """
    #     Cast model to the defined subclass
    #     """
    #     for name, clazz in DataLocation.SUBCLASS_OBJECT_CHOICES.items():
    #         try:
    #             self = getattr(self, name)
    #             break
    #         except clazz.DoesNotExist:
    #             pass
    #     return self
    #
    # def uncast(self):
    #     try:
    #         self = self.datalocation_ptr
    #     except AttributeError:
    #         pass
    #     return self
    #
    # @property
    # def display(self):
    #     return "not set"
    #
    # @property
    # def attrs(self):
    #     return {}



# class LocationHolder(DataLocation):
#     """
#     A location of the data.
#     Should be temporary as location granularity would increase.
#     """
#     location = TextFieldWithInputWidget(
#         verbose_name='Location of the data'
#     )
#
#     def __str__(self):
#         return self.display
#
#     @property
#     def display(self):
#         return self.location
#
#     @property
#     def attrs(self):
#         return {
#             'location': self.location
#         }
#
#
# class FilePath(DataLocation):
#     """
#     A data location on the filesystem
#     """
#     path = TextFieldWithInputWidget(
#         verbose_name='Absolute path to the file or directory'
#     )
#
#     @property
#     def display(self):
#         return f'{self.path}'
#
#     @property
#     def attrs(self):
#         return {
#             'path': self.path
#         }
#
#
# class CloudShare(DataLocation):
#     """
#     A data location on the cloud, like Owncloud, Dropbox, ...
#     """
#     name = TextFieldWithInputWidget(
#         verbose_name='Name of the account owner'
#     )
#
#     path = TextFieldWithInputWidget(
#         verbose_name='Absolute path to the file or directory'
#     )
#
#     @property
#     def display(self):
#         return f'{self.name} : {self.path}'
#
#     @property
#     def attrs(self):
#         return {
#             'name': self.name,
#             'path': self.path
#         }
#
#
# class Station(DataLocation):
#     """
#     A data location on a personal device like a desktop or laptop.
#     """
#     identifier = TextFieldWithInputWidget(
#         verbose_name='Identifier of the station'
#     )
#
#     owner = TextFieldWithInputWidget(
#         verbose_name="Owner's name"
#     )
#
#     path = TextFieldWithInputWidget(
#         verbose_name='Absolute path to the file or directory'
#     )
#
#     @property
#     def display(self):
#         return f'{self.owner} : {self.identifier} : {self.path}'
#
#     @property
#     def attrs(self):
#         return {
#             'identifier': self.identifier,
#             'owner': self.owner,
#             'path': self.path
#         }
#
#
# class ExternalDevice(DataLocation):
#     """
#     An external device
#     """
#     owner = TextFieldWithInputWidget(
#         verbose_name="Owner's name"
#     )
#
#     path = TextFieldWithInputWidget(
#         verbose_name='Absolute path to the file or directory'
#     )
#
#     additional_information = models.TextField(
#         verbose_name="Any additionnal information that can help to find the data."
#     )
#
#     @property
#     def display(self):
#         return f'{self.owner}: {self.path}'
#
#     @property
#     def attrs(self):
#         return {
#             'owner': self.owner,
#             'path': self.path,
#             'additional information': self.additional_information
#         }
#
#
# class Other(DataLocation):
#     """
#     An other storage location
#     """
#     location = TextFieldWithInputWidget(
#         verbose_name='Where is the data.'
#     )
#
#     additional_information = models.TextField(
#         verbose_name="Any additionnal information that can help to find the data."
#     )
#
#     @property
#     def display(self):
#         return f'{self.location}'
#
#     @property
#     def attrs(self):
#         return {
#             'name': self.name,
#             'path': self.path,
#             'additional information': self.additional_information
#         }
