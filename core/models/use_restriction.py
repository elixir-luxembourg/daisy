from django.db import models

from model_utils import Choices

from . import RestrictionClass
from .utils import CoreModel


USE_RESTRICTION_CHOICES = Choices(
    ("PROHIBITION", "PROHIBITION"),
    ("OBLIGATION", "OBLIGATION"),
    ("PERMISSION", "PERMISSION"),
    ("CONSTRAINED_PERMISSION", "CONSTRAINED_PERMISSION"),
)


class UseRestriction(CoreModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]

    data_declaration = models.ForeignKey(
        "core.DataDeclaration",
        related_name="data_use_restrictions",
        null=False,
        on_delete=models.CASCADE,
        help_text="The data declaration to which this restriction applies.",
    )

    # Use Category
    restriction_class = models.CharField(
        verbose_name="Use Category",
        max_length=20,
        blank=True,
        null=True,
        help_text="Select the GA4GH code for the restriction.  Refer to 'GA4GH Consent Codes' for a detailed explanation of each.",
    )

    # Use Restriction Note
    notes = models.TextField(
        verbose_name="Use Restriction note",
        blank=True,
        null=True,
        help_text="Provide a free text description of the restriction.",
    )

    # Use Category note
    use_class_note = models.TextField(
        verbose_name="Use Category note",
        max_length=255,
        blank=True,
        null=True,
        help_text="A question asked when collecting the restriction class",
    )

    use_restriction_rule = models.TextField(
        verbose_name="Use Restriction Rule",
        choices=USE_RESTRICTION_CHOICES,
        default=USE_RESTRICTION_CHOICES.PROHIBITION,
        blank=False,
        null=False,
        max_length=64,
    )

    def clone_shallow(self):
        clone = UseRestriction()
        clone.restriction_class = self.restriction_class
        clone.notes = self.notes
        clone.use_class_note = self.use_class_note
        clone.use_restriction_rule = self.use_restriction_rule
        return clone

    def __str__(self):
        if self.data_declaration_id is None:
            title = "(no DataDeclaration coupled"
        else:
            title = self.data_declaration.title or "(DataDeclaration with no title)"
        return f"{self.restriction_class} - on {title} - {self.notes}"

    def to_dict(self):
        """
        Used for import/export - the keys are conformant to the schema
        """
        return {
            "use_class": self.restriction_class,
            "use_class_label": RestrictionClass.objects.get(
                code=self.restriction_class
            ).name,
            "use_class_note": self.use_class_note,
            "use_restriction_note": self.notes,
            "use_restriction_rule": self.use_restriction_rule,
        }

    def serialize(self):
        """
        Used for forms - the keys are conformant to the django model
        """
        return {
            "restriction_class": self.restriction_class,
            "use_class_note": self.use_class_note,
            "notes": self.notes,
            "use_restriction_rule": self.use_restriction_rule,
        }
