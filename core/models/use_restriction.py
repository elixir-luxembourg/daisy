import reversion
from django.db import models

from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register(follow=('data_declaration',))
class UseRestriction(CoreModel):
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']



    data_declaration = models.ForeignKey("core.DataDeclaration",
                                         related_name="data_use_restrictions",
                                         null=False,
                                         on_delete=models.CASCADE,
                                         help_text='The data declaration to which this restriction applies.')

    restriction_class = models.CharField(verbose_name='Restriction class',
                                         max_length=20,
                                          blank=True,
                                          null=True,
                                          help_text='Select the GA4GH code for the restriction.  Refer to \'GA4GH Consent Codes\' for a detailed explanation of each.')

    notes = models.TextField(verbose_name='Description',
                                     max_length=255,
                                     blank=True,
                                     null=True,
                                     help_text='Provide a free text description of the restriction.')



    def clone_shallow(self):
        clone = UseRestriction()
        clone.restriction_class = self.restriction_class
        clone.notes = self.notes
        return clone

    def __str__(self):
        return "{} - {}".format(self.restriction_class, self.notes)
