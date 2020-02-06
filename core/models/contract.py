from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core import constants
from .contact import Contact
from .partner import Partner
from .utils import CoreModel, COMPANY


class PartnerRole(CoreModel):
    class Meta:
        app_label = 'core'

    partner = models.ForeignKey('core.Partner',
                                verbose_name='Partner', related_name="partners_roles",
                                on_delete=models.CASCADE, blank=False, null=False)

    roles = models.ManyToManyField("core.GDPRRole",
                                   verbose_name='Partner roles',
                                   related_name='partners_roles',
                                   )

    contacts = models.ManyToManyField('core.Contact',
                                      verbose_name='Contacts',
                                      related_name="partners_roles",
                                      blank=False,
                                      )

    contract = models.ForeignKey('core.Contract',
                                 verbose_name='Contract',
                                 related_name="partners_roles",
                                 on_delete=models.CASCADE,
                                 blank=False,
                                 null=False)


class Contract(CoreModel):
    """
    Represents a contract, which can be source or recipient of dataset if it's not internal project
    """

    class Meta:
        app_label = 'core'
        get_latest_by = "added"
        ordering = ['added']
        permissions = (
            (constants.Permissions.ADMIN.value, 'Responsible of the project'),
            (constants.Permissions.EDIT.value, 'Edit the project'),
            (constants.Permissions.DELETE.value, 'Delete the project'),
            (constants.Permissions.VIEW.value, 'View the project'),
            (constants.Permissions.PROTECTED.value, 'View the protected elements'),
        )

    class AppMeta:
        help_text = "Contracts are agreements among partners.  Contracts are established by " \
                    "one or more mutually-signed legal documents such as Data Sharing Agreements, Consortium Agreements," \
                    " Material Transfer Agreements."

    local_custodians = models.ManyToManyField('core.User',
                                              blank=False,
                                              related_name='contracts',
                                              verbose_name='Local custodians',
                                              help_text='Custodians are the local parties to the contract. Custodian list must include all the PIs, whose names appear on the contract.')

    comments = models.TextField(verbose_name='Other comments', blank=True, null=True,
                                help_text='Provide remarks on this contract.')

    legal_documents = GenericRelation('core.Document', related_query_name='contracts',
                                      verbose_name='Document(s)',
                                      help_text='A contract would be associated with one or more documents. You can either upload documents or provide links to them, if they are in an external document management system.')

    project = models.ForeignKey(
        'core.Project',
        related_name='contracts',
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        verbose_name='Project',
        help_text='If this Contract is signed within the scope of particular Project, then it should be denoted here.'
    )

    company_roles = models.ManyToManyField("core.GDPRRole", verbose_name='{}''s roles'.format(COMPANY),
                                           related_name="contracts",
                                           help_text='Please select the GDPR roles assumed by {} as per this contract.'.format(
                                               COMPANY))

    # metadata = JSONField(null=True, blank=True, default=dict)

    def add_partner_with_role(self, partner, role, contact=None):
        partner_role = self.partners_roles.create(partner=partner)
        if contact:
            partner_role.contacts.add(contact)
        partner_role.roles.add(role)

    @property
    def partners(self):
        return Partner.objects.filter(partners_roles__contract=self)

    @property
    def contacts(self):
        return Contact.objects.filter(partners_roles__contract=self)

    def __str__(self):
        return self.short_name()

    def short_name(self):
        partners_list = ", ".join([p.name for p in self.partners.all()]) or "Undefined partner(s)"
        if self.project:
            project_name = self.project.acronym if len(self.project.acronym) else self.project.title
        else:
            project_name = "Undefined project"

        return f'Contract with {partners_list} - "{project_name}"'
