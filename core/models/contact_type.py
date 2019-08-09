import reversion
from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register()
class ContactType(CoreModel):
    """
    ContactType tries to model type of the contact.
    For example:
        'PI' or 'lawyer'
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    name = TextFieldWithInputWidget(max_length=128,
                                    blank=False,
                                    verbose_name='Name of the contact type', unique=True)

    def __str__(self):
        return "{}".format(self.name)
