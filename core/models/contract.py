from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse

from core import constants
from core.permissions.mapping import PERMISSION_MAPPING
from .contact import Contact
from .partner import Partner, HomeOrganisation
from .utils import CoreModel


class PartnerRole(CoreModel):
    class Meta:
        app_label = "core"

    partner = models.ForeignKey(
        "core.Partner",
        verbose_name="Partner",
        related_name="partners_roles",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )

    roles = models.ManyToManyField(
        "core.GDPRRole",
        verbose_name="Partner roles",
        related_name="partners_roles",
    )

    contacts = models.ManyToManyField(
        "core.Contact",
        verbose_name="Contacts",
        related_name="partners_roles",
        blank=False,
    )

    contract = models.ForeignKey(
        "core.Contract",
        verbose_name="Contract",
        related_name="partners_roles",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )

    comments = models.TextField(
        verbose_name="Comments",
        blank=True,
        null=True,
        help_text="Provide remarks on this partner involvement.",
    )

    def __str__(self):
        return self.short_name()

    def short_name(self):
        partner = self.partner.name
        project_acronym = (
            self.contract.project.acronym if self.contract.project else "unknown"
        )
        if len(self.roles.all()):
            roles = "as " + "/".join([str(role) for role in self.roles.all()])
        else:
            roles = ""
        return f"{partner} on {project_acronym} {roles}"


class Contract(CoreModel):
    """
    Represents a contract, which can be source or recipient of dataset if it's not internal project
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        permissions = PERMISSION_MAPPING[
            "Contract"
        ]  # Adds PROTECTED and ADMIN permissions to Contract

    class AppMeta:
        help_text = (
            "Contracts are agreements among partners.  Contracts are established by "
            "one or more mutually-signed legal documents such as Data Sharing Agreements, Consortium Agreements,"
            " Material Transfer Agreements."
        )

    name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Short name",
        help_text="Select a meaningful name for your contract",
    )

    local_custodians = models.ManyToManyField(
        "core.User",
        blank=False,
        related_name="contracts",
        verbose_name="Local custodians",
        help_text="Custodians are the local parties to the contract. Custodian list must include all the PIs, whose names appear on the contract.",
    )

    comments = models.TextField(
        verbose_name="Other comments",
        blank=True,
        null=True,
        help_text="Provide remarks on this contract.",
    )

    legal_documents = GenericRelation(
        "core.Document",
        related_query_name="contracts",
        verbose_name="Document(s)",
        help_text="A contract would be associated with one or more documents. You can either upload documents or provide links to them, if they are in an external document management system.",
    )

    project = models.ForeignKey(
        "core.Project",
        related_name="contracts",
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        verbose_name="Project",
        help_text="If this Contract is signed within the scope of particular Project, then it should be denoted here.",
    )

    # metadata = JSONField(null=True, blank=True, default=dict)
    def get_absolute_url(self):
        return reverse("contract", args=[str(self.pk)])

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

    @property
    def partner_roles(self):
        return PartnerRole.objects.filter(contract=self)

    def __str__(self):
        return self.name or self.short_name()

    def display_partners(self):
        partners = self.partners.all()
        if len(partners) > 2:
            partners_str = ', '.join(str(p) for p in partners[:2])
            return f"{partners_str} and {len(partners)-2} more..."
        return ', '.join(str(p) for p in partners) if partners else '-'

    def display_partners_tooltip(self):
        partners = self.partners.all()
        return ", ".join(str(p) for p in partners) if partners else ""

    def short_name(self):
        partners_list = (
            ", ".join([p.name for p in self.partners.all()]) or "Undefined partner(s)"
        )
        if self.project:
            project_name = (
                self.project.acronym
                if len(self.project.acronym)
                else self.project.title
            )
        else:
            project_name = "Undefined project"

        return f'Contract with {partners_list} - "{project_name}"'

    def to_dict(self):
        contact_dicts = []
        for lc in self.local_custodians.all():
            contact_dicts.append(
                {
                    "first_name": lc.first_name,
                    "last_name": lc.last_name,
                    "email": lc.email,
                    "role": "Principal_Investigator"
                    if lc.is_part_of(constants.Groups.VIP.name)
                    else "Researcher",
                    "affiliations": [HomeOrganisation().name],
                }
            )

        partners_dicts = []
        for partner_role in self.partner_roles:
            pd = {}
            pd["partner"] = partner_role.partner.name
            pd["partner_roles"] = [role.name for role in partner_role.roles.all()]
            pd["comments"] = partner_role.comments
            pd["contacts"] = [
                contact.to_dict() for contact in partner_role.contacts.all()
            ]
            partners_dicts.append(pd)

        base_dict = {
            "id": self.id,
            "name": self.name,
            "comments": self.comments,
            "project_id": self.project.id,
            "local_custodians": contact_dicts,
            "partners": partners_dicts,
        }
        return base_dict

    def serialize_to_export(self):
        import functools

        d = self.to_dict()

        local_custodians = map(
            lambda v: f"[{v['first_name']} {v['last_name']}, {v['email']}]",
            d["local_custodians"],
        )

        d["local_custodians"] = ",".join(local_custodians)

        partners = map(
            lambda v: f"[{v['partner']}, roles:{','.join(v['partner_roles'])}, comments:{v['comments']}]",
            d["partners"],
        )
        d["partners"] = ",".join(partners)

        if "project" in d and d["project"]:
            d["project"] = d["project"].title
        return d
