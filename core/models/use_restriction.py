from django.db import models

from model_utils import Choices
from .utils import CoreModel, TextFieldWithInputWidget


USE_RESTRICTION_CHOICES = Choices(
        ('CONSTRAINTS', 'CONSTRAINTS'),
        ('NO_CONSTRAINTS', 'NO_CONSTRAINTS'),
        ('FORBIDDEN', 'FORBIDDEN')
)


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
                                         
    # use_class after renaming
    restriction_class = models.CharField(verbose_name='Restriction class',
                                         max_length=20,
                                         blank=True,
                                         null=True,
                                         help_text='Select the GA4GH code for the restriction.  Refer to \'GA4GH Consent Codes\' for a detailed explanation of each.')

    # use_class_note after renaming
    notes = models.TextField(verbose_name='Description',
                             max_length=255,
                             blank=True,
                             null=True,
                             help_text='Provide a free text description of the restriction.')

    use_class_note = models.TextField(verbose_name='Use restriction class note',
                                      max_length=255,
                                      blank=True,
                                      null=True,
                                      help_text='A question asked when collecting the restriction class')

    use_restriction_rule = models.TextField(verbose_name='Does the rule forbid (FORBIDDEN), constraint (CONSTRAINTS) or have no constraints (NO_CONSTRAINTS)?',
                                            choices=USE_RESTRICTION_CHOICES,
                                            default=USE_RESTRICTION_CHOICES.NO_CONSTRAINTS,
                                            blank=False, 
                                            null=False,
                                            max_length=64)

    def clone_shallow(self):
        clone = UseRestriction()
        clone.restriction_class = self.restriction_class
        clone.notes = self.notes
        clone.use_class_note = self.use_class_note
        clone.use_restriction_rule = self.use_restriction_rule
        return clone

    def __str__(self):
        title = self.data_declaration.title or '(Data Declaration with no title)'
        return "{} - on {} - {}".format(self.restriction_class, title, self.notes)

    def to_dict(self):
        return {
            "use_class": self.restriction_class, 
            "use_class_note": self.use_class_note,
            "use_restriction_note": self.notes,
            "use_restriction_rule": self.use_restriction_rule
        }