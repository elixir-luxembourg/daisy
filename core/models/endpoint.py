import re

from django.db import models
from django.core.exceptions import ValidationError

from .utils import CoreModel, HashedField


class Endpoint(CoreModel):
    """
    Represents an endpoint for exposing/publishing data to the outside world. like a datacatalog instance.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["name"]

    name = models.CharField(
        max_length=128,
        verbose_name="Name",
        unique=True,
        help_text="* Please specify the name of the endpoint",
    )

    url_pattern = models.CharField(
        max_length=256,
        verbose_name="URL Pattern",
        blank=True,
        help_text="""
        Please specify the url pattern to the entity page and incorporate entity_id like the example:
        <h3>https://datacatalog.elixir-luxembourg.org/e/dataset/${entity_id}</h3>""",
    )

    api_key = HashedField(
        max_length=128,
        verbose_name="API Key",
        help_text="""
        * Please specify the API key to the endpoint, 
        head <a href='https://generate-random.org/api-key-generator?count=1&length=64&type=mixed-numbers&prefix=' target='_blank'> here </a>
        to generate a random key and keep it somewhere, we only store a hash.
        """,
    )

    def clean(self):
        """
        This function gets called from the Django admin before save so we use it to validate the url pattern and the api key.
        """

        re_pattern = r"^https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,7}/[a-zA-Z0-9-_/]*\${entity_id}[a-zA-Z0-9-_/]*$"
        if self.url_pattern and not re.match(re_pattern, self.url_pattern):
            raise ValidationError(
                "The URL pattern must contain the ${entity_id} placeholder and be a valid URL."
            )
        if self.api_key and len(self.api_key) < 64:
            raise ValidationError("The API key must be 64 characters long.")

    def __str__(self):
        return f"{self.name}"
