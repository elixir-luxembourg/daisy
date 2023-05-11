from django.db import models

from .utils import CoreModel


class Exposure(CoreModel):
    """
    Represents the exposure of a dataset to an endpoint with a request access form.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]

    endpoint = models.ForeignKey('core.Endpoint',
                                 verbose_name='Endpoint',
                                 on_delete=models.CASCADE,
                                 related_name='exposures',
                                 help_text='The endpoint to which the entity is exposed.')

    dataset = models.ForeignKey('core.Dataset',
                                verbose_name='Dataset',
                                on_delete=models.CASCADE,
                                related_name='exposures',
                                help_text='The dataset that is exposed.')

    form_id = models.IntegerField()

    created_by = models.ForeignKey('core.User',
                                   verbose_name='Created by',
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   help_text='Which User added this entry to DAISY', )
    
    @property
    def url(self):
        url = self.endpoint.url_pattern.replace('${entity_id}', str(self.dataset.unique_id))
        return url

    def __str__(self):
        return f'Exposure: {self.dataset}@{self.endpoint}'
