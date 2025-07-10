from .utils import CoreModel, TextFieldWithInputWidget


class ConditionClass(CoreModel):
    """
    Represents data use condition code. We currently populate this with GA4GH Consent Codes.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["name"]
        verbose_name = "Condition Class"
        verbose_name_plural = "Condition Classes"

    code = TextFieldWithInputWidget(
        max_length=20, blank=False, verbose_name="Code", unique=True
    )

    name = TextFieldWithInputWidget(
        max_length=120, blank=False, verbose_name="Name", unique=True
    )

    description = TextFieldWithInputWidget(
        max_length=500, blank=False, verbose_name="Description", unique=True
    )

    def __str__(self):
        return self.name
