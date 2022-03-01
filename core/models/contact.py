from datetime import datetime

from django.db import models

from core.models.access import Access
from core.models.contact_type import ContactType
from core.models.utils import CoreModel, TextFieldWithInputWidget


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
        verbose_name='Address'
    )

    email = models.EmailField(verbose_name='E-mail of the contact')

    first_name = TextFieldWithInputWidget(
        blank=False,
        verbose_name='First name of the contact'
    )

    last_name = TextFieldWithInputWidget(
        blank=False,
        verbose_name='Last name of the contact'
    )

    oidc_id = models.CharField(verbose_name='OIDC user identifier',
        blank=True,
        null=True,
        max_length=64,
        unique=True,
        help_text="Internal user identifier from OIDC's IdP"
    )

    partners = models.ManyToManyField(
        'core.Partner',
        related_name='contacts',
        verbose_name='Affiliation(s)',
        blank=False
    )

    phone = TextFieldWithInputWidget(max_length=32,
        blank=True,
        null=True,
        verbose_name='Phone'
    )

    type = models.ForeignKey(
        'core.ContactType',
        verbose_name='Type of the contact',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.type.name})"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        partners_dict = []
        for partner in self.partners.all():
            partners_dict.append({
                'acronym': partner.acronym,
                'name': partner.name
            })

        base_dict = {
            "pk": str(self.id),
            "email": self.email,
            "oidc_id": self.oidc_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
            "phone": self.phone,
            "type": self.type.name if self.type else '',
            "partners": partners_dict if len(partners_dict) else ''
        }
        return base_dict

    def serialize_to_export(self):
        import functools

        d = self.to_dict()

        if len(d['partners']):
            partners = map(lambda v: f"[{v['name']}]", d['partners'])
            d['partners'] = ','.join(partners)

        return d

    @classmethod
    def get_or_create(cls, email: str, oidc_id: str, resource: str):
        try:
            if cls.objects.filter(oidc_id=oidc_id).count() == 1:
                return cls.objects.get(oidc_id=oidc_id)
            if cls.objects.filter(email=email).count() == 1:
                return cls.objects.get(email=email)
            else:
                message = f'There are either zero, or 2 and more contacts with such `email` and `oidc_id`!'
                raise ValueError(message)
        except cls.DoesNotExist:
            contact_type = ContactType.objects.get_or_create(name='Other (imported from Keycloak)')
            new_object = cls(
                email=email, 
                first_name='IMPORTED BY REMS', 
                last_name='IMPORTED BY REMS',
                type=contact_type
            )
            new_object.save()
            return new_object

    def get_access_permissions(self):
        """
        Finds Accesses of the user, and returns a list of their dataset IDs 
        """
        return Access.find_for_contact(self)
        