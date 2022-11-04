from .utils import CoreModel, TextFieldWithInputWidget

from core import constants

class Publication(CoreModel):
    """
    Represents a citation string.
    They could contain DOI, except for really old ones.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']

        permissions = (
            (constants.Permissions.ADMIN.value, 'Can edit user permissions on Publication instances'),
            (constants.Permissions.EDIT.value, 'Can edit the Publication instances'),
            (constants.Permissions.DELETE.value, 'Can delete the Publication instances'),
            (constants.Permissions.VIEW.value, 'Can view Publication instances'),
            (constants.Permissions.PROTECTED.value, 'Can view/edit the protected elements of Publication instances'),
        )


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
