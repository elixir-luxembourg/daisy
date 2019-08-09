import reversion
from django.db import models

from .utils import CoreModel, TextFieldWithInputWidget

@reversion.register(follow=('type', 'parners'))
class Contact(CoreModel):
    """
    Contact represents a contact person.
    For instance:
        Mr. Adam Smith from uni.lu (adam.smith@uni.lu) (type: DPO)
        Ms. Amy Good from PUT Poznan (amy.good@put.poznan.pl) (type: PI)
    It's type is moved to another model in case "regular" values are not sufficient.
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']


    class AppMeta:
        help_text = "Contacts are people affiliated with Partner institutions. Collaborator PIs, Project Officers at the EU are examples of contacts."


    address = TextFieldWithInputWidget(
                               blank=True,
                               null=True,
                               verbose_name='Address')

    email = models.EmailField(verbose_name='E-mail of the contact')

    first_name = TextFieldWithInputWidget(blank=False,
                                  verbose_name='First name of the contact')

    last_name = TextFieldWithInputWidget(blank=False,
                                 verbose_name='Last name of the contact')

    phone = TextFieldWithInputWidget(max_length=32,
                             blank=True,
                             null=True,
                             verbose_name='Phone')

    type = models.ForeignKey('core.ContactType',
                             verbose_name='Type of the contact',
                             on_delete=models.CASCADE)

    partners = models.ManyToManyField('core.Partner',
                                related_name='contacts',
                                verbose_name='Affiliation(s)',
                                blank=False)


    def __str__(self):
        return "{} {} ({})".format(self.first_name, self.last_name, self.type.name)



    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)
