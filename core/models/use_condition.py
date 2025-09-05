from django.db import models

from model_utils import Choices

from . import ConditionClass
from .utils import CoreModel


USE_CONDITION_CHOICES = Choices(
    ("PROHIBITION", "PROHIBITION"),
    ("OBLIGATION", "OBLIGATION"),
    ("PERMISSION", "PERMISSION"),
    ("CONSTRAINED_PERMISSION", "CONSTRAINED_PERMISSION"),
)


class UseCondition(CoreModel):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        verbose_name = "Use Condition"
        verbose_name_plural = "Use Conditions"

    data_declaration = models.ForeignKey(
        "core.DataDeclaration",
        related_name="data_use_conditions",
        null=False,
        on_delete=models.CASCADE,
        help_text="The data declaration to which this condition applies.",
    )

    # Use Category
    condition_class = models.CharField(
        verbose_name="Use Category",
        max_length=20,
        blank=True,
        null=True,
        help_text="Select the GA4GH code for the condition.  Refer to 'GA4GH Consent Codes' for a detailed explanation of each.",
    )

    # Use Condition Note
    notes = models.TextField(
        verbose_name="Use Condition note",
        blank=True,
        null=True,
        help_text="Provide a free text description of the condition.",
    )

    # Use Category note
    use_class_note = models.TextField(
        verbose_name="Use Category note",
        max_length=255,
        blank=True,
        null=True,
        help_text="A question asked when collecting the condition class",
    )

    use_condition_rule = models.TextField(
        verbose_name="Use Condition Rule",
        choices=USE_CONDITION_CHOICES,
        default=USE_CONDITION_CHOICES.PROHIBITION,
        blank=False,
        null=False,
        max_length=64,
    )

    def clone_shallow(self):
        clone = UseCondition()
        clone.condition_class = self.condition_class
        clone.notes = self.notes
        clone.use_class_note = self.use_class_note
        clone.use_condition_rule = self.use_condition_rule
        return clone

    def __str__(self):
        if self.data_declaration_id is None:
            title = "(no DataDeclaration coupled"
        else:
            title = self.data_declaration.title or "(DataDeclaration with no title)"
        return f"{self.condition_class} - on {title} - {self.notes}"

    def to_dict(self):
        """
        Used for import/export - the keys are conformant to the schema
        """
        return {
            "use_class": self.condition_class,
            "use_class_label": ConditionClass.objects.get(
                code=self.condition_class
            ).name,
            "use_class_note": self.use_class_note,
            "use_condition_note": self.notes,
            "use_condition_rule": self.use_condition_rule,
        }

    def serialize(self):
        """
        Used for forms - the keys are conformant to the django model
        """
        return {
            "condition_class": self.condition_class,
            "use_class_note": self.use_class_note,
            "notes": self.notes,
            "use_condition_rule": self.use_condition_rule,
        }
