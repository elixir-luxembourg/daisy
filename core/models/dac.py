from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError

from core.permissions.mapping import PERMISSION_MAPPING
from .utils import CoreModel


class DAC(CoreModel):
    """
    Represents a Data Access Committee (DAC) that reviews and approves data access requests.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        permissions = PERMISSION_MAPPING[
            "DAC"
        ]  # Adds PROTECTED and ADMIN permissions to DAC

    class AppMeta:
        help_text = "Data Access Committees (DACs) are responsible for reviewing and approving data access requests."

    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="The title of the Data Access Committee.",
        blank=False,
        null=False,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="A brief description of the DAC's purpose and scope.",
    )

    contract = models.ForeignKey(
        "core.Contract",
        related_name="dac",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name="Contract",
        help_text="The contract under which this Data Access Committee operates.",
    )

    local_custodians = models.ManyToManyField(
        "core.User",
        related_name="dac_custodians",
        verbose_name="Local custodians",
        blank=False,
        help_text="Local custodians are the members of the DAC who are responsible for managing data access requests.",
    )

    members = models.ManyToManyField(
        "core.Contact",
        through="DacMembership",
        blank=True,
    )

    @property
    def project(self):
        """
        Returns the projects associated with the DAC's contract.
        """
        return self.contract.project

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("dac", args=[str(self.pk)])

    def get_full_url(self):
        """
        Returns the full URL to access this DAC instance.
        """
        return "%s://%s%s" % (
            settings.SERVER_SCHEME,
            settings.SERVER_URL,
            self.get_absolute_url(),
        )

    def to_dict(self):
        return {
            "pk": str(self.id),
            "title": self.title,
            "description": self.description,
            "contract": self.contract.to_dict(),
            "local_custodians": [
                custodian.to_dict() for custodian in self.local_custodians.all()
            ],
            "members": [member.to_dict() for member in self.members.all()],
        }

    def clean(self):
        super().clean()
        if self.pk and not self.local_custodians.exists():
            raise ValidationError(
                {"local_custodians": "At least one local custodian is required."}
            )

    def delete(self, *args, **kwargs):
        raise ValidationError("DAC objects cannot be deleted.")


class DacMembership(CoreModel):
    contact = models.ForeignKey("core.Contact", on_delete=models.CASCADE)
    dac = models.ForeignKey(DAC, on_delete=models.CASCADE)
    remark = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["contact", "dac"], name="unique_person_group"
            )
        ]
