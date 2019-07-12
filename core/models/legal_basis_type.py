from .utils import CoreModel, TextFieldWithInputWidget


class LegalBasisType(CoreModel):
    """
    Represents categories of legal basis. We populate it with those defined in the GDPR.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['name']

    code = TextFieldWithInputWidget(max_length=20,
                                    blank=False,
                                    verbose_name='Code', unique=True)

    name = TextFieldWithInputWidget(max_length=120,
                                    blank=False,
                                    verbose_name='Name', unique=True)

    def __str__(self):
        return "{} [{}]".format(self.name, self.code)
