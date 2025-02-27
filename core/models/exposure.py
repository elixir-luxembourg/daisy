from django.db import models
from django.utils.timezone import now

from .utils import CoreModel


class Exposure(CoreModel):
    """
    Represents the exposure of a dataset to an endpoint with a request access form.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]

    endpoint = models.ForeignKey(
        "core.Endpoint",
        verbose_name="Endpoint",
        on_delete=models.CASCADE,
        related_name="exposures",
        help_text="The endpoint to which the entity is exposed.",
    )

    dataset = models.ForeignKey(
        "core.Dataset",
        verbose_name="Dataset",
        on_delete=models.CASCADE,
        related_name="exposures",
        help_text="The dataset that is exposed.",
    )

    form_id = models.IntegerField(help_text="The REMS form of the dataset.")

    form_name = models.CharField(
        blank=False, null=True, max_length=500, help_text="The REMS form name."
    )

    created_by = models.ForeignKey(
        "core.User",
        verbose_name="Created by",
        on_delete=models.SET_NULL,
        null=True,
        help_text="Which User added this entry to DAISY",
    )

    is_deprecated = models.BooleanField(default=False)
    deprecated_at = models.DateTimeField(null=True, blank=True)
    deprecation_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for deprecating this exposure",
    )

    @property
    def url(self):
        url = self.endpoint.url_pattern.replace(
            "${entity_id}", str(self.dataset.elu_accession)
        )
        return url

    def __str__(self):
        return f"Exposure: {self.dataset}@{self.endpoint}"

    def delete(self, deprecation_reason: str = None):
        self.is_deprecated = True
        self.deprecated_at = now()
        if deprecation_reason:
            self.deprecation_reason = deprecation_reason
        self.save()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "endpoint"],
                condition=models.Q(is_deprecated=False),
                name="unique_active_dataset_endpoint",
            ),
        ]
