from django.db import models

from .utils import CoreModel


class Share(CoreModel):
    """
    Represents the events concerning a dataset.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]

    data_log_type = models.ForeignKey(
        "core.DataLogType",
        null=True,
        verbose_name="Logbook entry category.",
        blank=False,
        on_delete=models.SET_NULL,
    )

    partner = models.ForeignKey(
        "core.Partner",
        verbose_name="Involved partner",
        related_name="shares",
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
        help_text="The Partner involved in the data event.",
    )

    share_notes = models.TextField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name="Remarks",
        help_text="Please state here any remarks e.g. safeguards, technical measures.",
    )

    granted_on = models.DateField(
        verbose_name="Date",
        blank=True,
        null=True,
        help_text="The date on which the data event occured.",
    )

    dataset = models.ForeignKey(
        "core.Dataset",
        verbose_name="Dataset",
        related_name="shares",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        help_text="The dataset that has been shared.",
    )

    data_declarations = models.ManyToManyField(
        "core.DataDeclaration",
        blank=True,
        related_name="share_records",
        verbose_name="Scope of transfer",
        help_text="The scope of this transfer. Leave empty if the all data declarations were transferred.",
    )

    contract = models.ForeignKey(
        "core.Contract",
        verbose_name="Contract",
        related_name="shares",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="The contract that provides the legal basis for this event.",
    )

    def __str__(self):
        return f"Logbook entry for {self.dataset.title}"
