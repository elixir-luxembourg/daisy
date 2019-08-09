import reversion
from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register()
class Publication(CoreModel):
    """
    Represents a citation string.
    They could contain DOI, except for really old ones.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

    # Citation string, with authors, title, publication year etc.
    citation = TextFieldWithInputWidget(blank=False,
                                        verbose_name='Citation string')

    # Digital Object Identifier
    doi = TextFieldWithInputWidget(verbose_name='DOI (Digital Object Identifier)',
                                   max_length=64,
                                   blank=True,
                                   null=True)

    def __str__(self):
        return self.citation[:64] + ("..." if len(self.citation) > 64 else "")
