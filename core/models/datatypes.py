import reversion
from django.db import models

from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register()
class DataType(CoreModel):
    """
    Objects of this class represent tree structure of data types
    """
    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['name']

    name = TextFieldWithInputWidget(blank=False, verbose_name='Data type')
    parent = models.ForeignKey(to="core.DataType",
                               blank=True,
                               null=True,
                               on_delete=models.SET_NULL)

    def __str__(self):
        return self.name
