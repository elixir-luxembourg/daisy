import datetime
import typing
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.module_loading import import_string
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

from core import constants
from core.permissions.mapping import PERMISSION_MAPPING
from notification import NotifyMixin
from notification.models import NotificationVerb, Notification
from core.utils import DaisyLogger

from .utils import CoreTrackedModel, COMPANY
from .partner import HomeOrganisation


if typing.TYPE_CHECKING:
    User = settings.AUTH_USER_MODEL


logger = DaisyLogger(__name__)


class Project(CoreTrackedModel, NotifyMixin):
    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        permissions = PERMISSION_MAPPING[
            "Project"
        ]  # Adds PROTECTED and ADMIN to permissions on Project

    class AppMeta:
        help_text = (
            "Projects are time-limited research activities with associated documentation on ethical, "
            "legal and administrative processes followed for their setup."
        )

    acronym = models.CharField(
        blank=False,
        null=False,
        verbose_name="Acronym",
        unique=True,
        max_length=200,
        help_text="Acronym is the short project name.",
    )

    cner_notes = models.TextField(
        verbose_name="National ethics approval notes",
        default="",
        help_text="Provide notes on national ethics approval. If it does not exist, please state justifications here.",
        blank=True,
        null=True,
    )

    contacts = models.ManyToManyField(
        "core.Contact",
        related_name="projects",
        verbose_name="Contact persons",
        help_text="Contacts are project related people other than local personnel e.g. Project Officer at the European Commission can be recorded as a Contact.",
        blank=True,
    )

    comments = models.TextField(
        verbose_name="Other comments",
        blank=True,
        null=True,
        help_text="Any remarks other than the project description can be provided here.",
    )

    company_personnel = models.ManyToManyField(
        "core.User",
        related_name="projects",
        verbose_name="{}" "s personnel".format(COMPANY),
        help_text="Please select local staff that is part of this project.",
        blank=True,
    )

    description = models.TextField(
        verbose_name="Lay summary",
        blank=True,
        null=True,
        help_text="Lay summary should provide a brief overview of project goals and approach. Lay summary may be displayed publicly if the project's data gets published in the data catalog",
    )

    disease_terms = models.ManyToManyField(
        "core.DiseaseTerm",
        related_name="projects_w_term",
        verbose_name="Disease terms",
        blank=True,
        help_text=mark_safe(
            'Provide keywords/terms that would characterize the disease that fall in project\'s scope. Please use terms from <a href="https://www.ebi.ac.uk/ols/ontologies/doid">HDO</a> ontology.'
        ),
    )

    end_date = models.DateField(
        verbose_name="End date",
        blank=True,
        help_text="Formal end date of project.",
        null=True,
    )

    erp_notes = models.TextField(
        verbose_name="Institutional ethics approval notes.",
        default="",
        help_text="Provide notes on institutional ethics approval. If it does not exist, please state justifications here.",
        blank=True,
        null=True,
    )

    funding_sources = models.ManyToManyField(
        "core.FundingSource",
        blank=True,
        related_name="projects_funded",
        verbose_name="Funding sources",
        help_text="Funding sources are national, international bodies or initiatives that have funded the research project.",
    )

    gene_terms = models.ManyToManyField(
        "core.GeneTerm",
        verbose_name="List of gene terms",
        blank=True,
        help_text=mark_safe(
            'Select one or more terms that would characterize the genes that fall in project\'s scope. Please use terms from <a href="https://www.genenames.org">HGNO ontology</a>.'
        ),
    )

    has_cner = models.BooleanField(
        default=False,
        verbose_name="Has National Ethics Approval?",
        help_text="Does the project have an ethics approval from a national body. E.g. In Luxembourg this would be Comité National d'Ethique de Recherche (CNER)",
    )

    has_erp = models.BooleanField(
        default=False,
        verbose_name="Has Institutional Ethics Approval?",
        help_text="Does the project have an ethics approval from an institutional body. E.g. At the LCSB this wuld be the Uni-Luxembourg Ethics Review Panel (ERP)",
    )

    includes_automated_profiling = models.BooleanField(
        default=False,
        blank=False,
        null=False,
        help_text="An example of profiling in biomedical research is the calculation of disease ratings or scores from clinical attributes.",
    )

    legal_documents = GenericRelation("core.Document", related_query_name="projects")

    umbrella_project = models.ForeignKey(
        "core.Project",
        null=True,
        blank=True,
        verbose_name="Umbrella project",
        help_text="If this project is part of a larger project, then please state the umbrella project here.",
        on_delete=models.CASCADE,
        related_name="child_projects",
    )

    phenotype_terms = models.ManyToManyField(
        "core.PhenotypeTerm",
        related_name="projects_w_term",
        verbose_name="Phenotype terms",
        blank=True,
        help_text=mark_safe(
            'Select one or more terms that would characterize the phenotypes that fall in project\'s scope. Please use terms from <a href="https://hpo.jax.org/">HPO ontology</a>.'
        ),
    )

    project_web_page = models.URLField(
        verbose_name="Project" "s URL page",
        help_text="If the project has a webpage, please provide its URL link here.",
        blank=True,
    )

    publications = models.ManyToManyField(
        "core.Publication", verbose_name="Project" "s publications", blank=True
    )

    start_date = models.DateField(
        verbose_name="Start date",
        blank=True,
        help_text="Formal start date of project.",
        null=True,
    )

    study_terms = models.ManyToManyField(
        "core.StudyTerm",
        blank=True,
        related_name="projects_w_type",
        verbose_name="Study features",
        help_text=mark_safe(
            'Select one or more features that would characterize the project. Please use terms from <a href="https://bioportal.bioontology.org/ontologies/EDDA">EDDA Study Designs Taxonomy</a>'
        ),
    )

    title = models.CharField(
        blank=False,
        null=True,
        verbose_name="Title",
        max_length=500,
        help_text="Title is the descriptive long project name.",
    )

    local_custodians = models.ManyToManyField(
        "core.User",
        related_name="project_set",
        verbose_name="Local custodians",
        help_text="Custodians are the local responsibles for the project. This list must include a PI.",
    )

    def __str__(self):
        return self.acronym or self.title or "undefined"

    def get_absolute_url(self):
        return reverse("project", args=[str(self.pk)])

    @property
    def is_published(self):
        return any(dataset.is_published for dataset in self.datasets.all())

    def to_dict(self):
        contact_dicts = []
        for contact in self.contacts.all():
            affiliations = []
            for aff in contact.partners.all():
                affiliations.append(aff.name)
            contact_dicts.append(
                {
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "role": contact.type.name,
                    "email": contact.email if contact.email else None,
                    "affiliations": affiliations,
                }
            )
        for lc in self.local_custodians.all():
            contact_dicts.append(
                {
                    "first_name": lc.first_name,
                    "last_name": lc.last_name,
                    "email": lc.email,
                    "role": "Principal_Investigator"
                    if lc.is_part_of(constants.Groups.VIP.value)
                    else "Researcher",
                    "affiliations": [HomeOrganisation().name],
                }
            )
        for cp in self.company_personnel.all():
            contact_dicts.append(
                {
                    "first_name": cp.first_name,
                    "last_name": cp.last_name,
                    "email": cp.email,
                    "role": "Researcher",
                    "affiliations": [HomeOrganisation().name],
                }
            )

        pub_dicts = []
        for pub in self.publications.all():
            pub_dicts.append(
                {
                    "citation": pub.citation if pub.citation else None,
                    "doi": pub.doi if pub.doi else None,
                }
            )

        base_dict = {
            "source": settings.SERVER_URL,
            "id_at_source": self.id.__str__(),
            "acronym": self.acronym,
            "external_id": self.elu_accession,
            "name": self.title if self.title else None,
            "description": self.description if self.description else None,
            "has_institutional_ethics_approval": self.has_erp,
            "has_national_ethics_approval": self.has_cner,
            "institutional_ethics_approval_notes": self.erp_notes
            if self.erp_notes
            else None,
            "national_ethics_approval_notes": self.cner_notes
            if self.cner_notes
            else None,
            "start_date": self.start_date.strftime("%Y-%m-%d")
            if self.start_date
            else None,
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
            "contacts": contact_dicts,
            "publications": pub_dicts,
            "metadata": self.scientific_metadata,
        }

        return base_dict

    def serialize_to_export(self):
        import functools

        d = self.to_dict()
        contacts = map(
            lambda v: f"[{v['first_name']} {v['last_name']}, {v['email']}]",
            d["contacts"],
        )
        d["contacts"] = ",".join(contacts)
        publications = map(
            lambda v: f"[{v['citation']}, {v['doi']}]", d["publications"]
        )
        d["publications"] = ",".join(publications)
        return d

    def publish(self):
        """
        Publishes the project.
        """
        if not self.is_published:
            self.is_published = True
            self.save()

    def save(self, *args, **kwargs):
        if self._state.adding and not self.elu_accession:
            generate_id_function_path = getattr(settings, "IDSERVICE_FUNCTION", None)
            if generate_id_function_path:
                generate_id_function = import_string(generate_id_function_path)
                self.elu_accession = generate_id_function(self)

            if not self.elu_accession:
                raise ValueError(
                    "Failed to generate 'elu_accession', object will not be saved."
                )

        super().save(*args, **kwargs)

    @staticmethod
    def get_notification_recipients():
        """
        Get distinct users that are local custodian of a project.
        """

        return get_user_model().objects.filter(Q(project_set__isnull=False)).distinct()

    @classmethod
    def make_notifications_for_user(
        cls, day_offset: timedelta, exec_date: datetime.date, user: "User"
    ):
        for project in user.project_set.all():
            # Project start date
            if project.start_date and project.start_date - day_offset == exec_date:
                cls.notify(user, project, NotificationVerb.start)
            # Project end date
            if project.end_date and project.end_date - day_offset == exec_date:
                cls.notify(user, project, NotificationVerb.end)

    @staticmethod
    def notify(user: "User", obj: "Project", verb: "NotificationVerb"):
        """
        Notifies concerning users about the entity.
        """
        dispatch_by_email = user.notification_setting.send_email
        dispatch_in_app = user.notification_setting.send_in_app

        if verb == NotificationVerb.start:
            msg = f"The project {obj.title} is starting."
            on = obj.start_date
        else:
            msg = f"The project {obj.title} is ending."
            on = obj.end_date

        logger.info(f"Creating a notification for {user} : {msg}")

        Notification.objects.create(
            recipient=user,
            verb=verb,
            message=msg,
            on=on,
            dispatch_by_email=dispatch_by_email,
            dispatch_in_app=dispatch_in_app,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
        ).save()


# faster lookup for permissions
# https://django-guardian.readthedocs.io/en/stable/userguide/performance.html#direct-foreign-keys
class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)
