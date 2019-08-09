import reversion
from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register()
class DocumentType(CoreModel):
    """
    Represents document type - for example CNER Approval
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    name = TextFieldWithInputWidget(max_length=128,
                                    blank=False,
                                    verbose_name='Name of the type of the document')

    def __str__(self):
        return "{}".format(self.name)
