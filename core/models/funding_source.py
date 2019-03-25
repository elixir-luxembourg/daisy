from .utils import CoreModel, TextFieldWithInputWidget


class FundingSource(CoreModel):
    """
    Represents funding organization
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['name']

    name = TextFieldWithInputWidget(max_length=255,
                                    blank=False,
                                    verbose_name='Funding source''s name', unique=True)

    def __str__(self):
        return self.name
