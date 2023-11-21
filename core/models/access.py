import logging
import typing

from datetime import datetime, date, timedelta
from typing import List

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, ObjectDoesNotExist, Count, signals

from enumchoicefield import EnumChoiceField, ChoiceEnum

from .utils import CoreModel, CoreNotifyMeta
from notification import NotifyMixin
from notification.models import NotificationVerb, Notification
from core.utils import DaisyLogger

from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField

if typing.TYPE_CHECKING:
    User = settings.AUTH_USER_MODEL


logger = DaisyLogger(__name__)


class StatusChoices(ChoiceEnum):
    precreated = "Pre-created"
    active = "Active"
    suspended = "Suspended"
    terminated = "Terminated"


class Access(CoreModel, NotifyMixin, metaclass=CoreNotifyMeta):
    """
    Represents the access given to an internal (LCSB) entity over data storage locations.
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["added"]
        constraints = [
            models.CheckConstraint(
                check=(Q(user__isnull=False) & Q(contact__isnull=True))
                | (Q(user__isnull=True) & Q(contact__isnull=False))
                | (Q(user__isnull=True) & Q(contact__isnull=True)),
                name="user_or_contact_only",
            )
        ]

    @classmethod
    def expire_accesses(cls, upper_date: date) -> None:
        """
        Set the status of Access objects with an expiration date lower than given `upper_date`
        to terminated

        @param upper_date: Date threshold.
        """
        accesses_to_expire = (
            cls.objects.filter(grant_expires_on__lt=upper_date)
            .exclude(
                status=StatusChoices.terminated,
            )
            .all()
        )
        for access in accesses_to_expire:
            logger.debug(
                f"Expiring access {access.pk} because expiration date ({access.grant_expires_on}) is lower than {upper_date.strftime('%Y-%m-%d')}"
            )
            access.status = StatusChoices.terminated
            access.access_notes = "Automatically terminated"
            # Necessary to manually send the signal because bulk_update does not use object.save()
            # Without this, auditlog cannot create a LogEntry for the change of status
            signals.pre_save.send(
                sender=cls,
                instance=access,
                created=False,
                raw=True,
                update_fields=("status", "access_notes"),
            )
        cls.objects.bulk_update(accesses_to_expire, ["status", "access_notes"])
        logger.debug("Accesses expired successfully")

    def clean(self):
        if self.user and self.contact:
            raise ValidationError(
                "The Access is granted either to a User, or to a Contact. If you need both, please create two separate entries."
            )

    history = AuditlogHistoryField()
    access_notes = models.TextField(
        null=False,
        blank=False,
        max_length=255,
        verbose_name="Remarks",
        help_text="Remarks on why and how access was given, what is the purpose of use.",
    )

    contact = models.ForeignKey(
        "core.Contact",
        verbose_name="Contact that has the access",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Use either `contact` or `user`",
    )

    created_by = models.ForeignKey(
        "core.User",
        verbose_name="Created by",
        on_delete=models.CASCADE,
        help_text="Which User added this entry to DAISY",
        blank=True,
        null=True,
    )

    dataset = models.ForeignKey(
        "core.Dataset",
        verbose_name="Dataset",
        related_name="accesses",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        help_text="The dataset to which access is given.",
    )

    defined_on_locations = models.ManyToManyField(
        "core.DataLocation",
        blank=True,
        related_name="accesses",
        verbose_name="Data Locations",
        help_text="The dataset locations on which access is defined.",
    )

    grant_expires_on = models.DateField(
        verbose_name="Grant expires on",
        blank=True,
        null=True,
        help_text="The date on which data access will expire.",
    )

    granted_on = models.DateField(
        verbose_name="Granted on",
        blank=True,
        null=True,
        help_text="The date on which data access was granted.",
    )

    project = models.ForeignKey(
        "core.Project",
        related_name="accesses_to_existing_datasets",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Project",
        help_text="If the access was given in the scope of a particular Project please specify.",
    )

    status = EnumChoiceField(
        StatusChoices,
        blank=False,
        null=False,
        default=StatusChoices.precreated,
        help_text="The status of the Access",
    )

    user = models.ForeignKey(
        "core.User",
        related_name="accesses",
        verbose_name="User that has the access",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Use either `contact` or `user`",
    )

    was_generated_automatically = models.BooleanField(
        verbose_name="Was created automatically",
        default=False,
        help_text="Was the entry generated automatically, e.g. by REMS?",
    )

    def __str__(self):
        try:
            if self.contact:
                return f"Access ({self.status}) to dataset {self.dataset.title} given to a contact: {self.contact}/{self.access_notes}"
            else:
                return f"Access ({self.status}) to dataset {self.dataset.title} given to a user: {self.user}/{self.access_notes}"
        except ObjectDoesNotExist as e:
            return f"Access ({self.status}) to dataset {self.dataset.title} given to a deleted contact or user: {self.access_notes}"

    def delete(self, force: bool = False):
        self.status = StatusChoices.terminated
        self.save()
        if force:
            super().delete()

    @property
    def display_locations(self):
        return "\n".join([str(loc) for loc in self.defined_on_locations.all()])

    @classmethod
    def find_for_user(cls, user) -> List[str]:
        accesses = cls.objects.annotate(c=Count("dataset__exposures")).filter(
            user=user, c__gt=0
        )
        return cls._filter_expired(accesses)

    @classmethod
    def find_for_contact(cls, contact) -> List[str]:
        accesses = cls.objects.annotate(c=Count("dataset__exposures")).filter(
            contact=contact, c__gt=0
        )
        return cls._filter_expired(accesses)

    @staticmethod
    def _filter_expired(accesses) -> List[str]:
        # For the performance reasons it does not use is active

        # The ones that are not expired yet
        non_expired_accesses = accesses.filter(
            grant_expires_on__gte=datetime.now(), status=StatusChoices.active
        )
        non_expired_accesses_names = [
            access.dataset.elu_accession for access in non_expired_accesses
        ]

        # The ones that don't have the expiration date
        accesses_without_expiration = accesses.filter(
            grant_expires_on__isnull=True, status=StatusChoices.active
        )
        accesses_without_expiration_names = [
            access.dataset.elu_accession for access in accesses_without_expiration
        ]

        # Remove the duplicates
        return list(set(non_expired_accesses_names + accesses_without_expiration_names))

    def is_active(self):
        if self.status != StatusChoices.active:
            return False

        if self.grant_expires_on is not None and self.grant_expires_on < datetime.now():
            return False

        return True

    def display_name(self) -> str:
        return f"{self.dataset}|{self.user or self.contact}"

    def get_absolute_url(self) -> str:
        return self.dataset.get_absolute_url()

    @staticmethod
    def get_notification_recipients():
        """
        Get distinct users that are local custodian of a dataset or a project.
        """

        return (
            get_user_model()
            .objects.filter(Q(datasets__isnull=False) | Q(project_set__isnull=False))
            .distinct()
        )

    @classmethod
    def make_notifications_for_user(
        cls, day_offset: timedelta, exec_date: date, user: "User"
    ):
        # Considering users that are indirectly responsible for the dataset (through projects)
        possible_datasets = set(user.datasets.all())
        possible_datasets.update(
            [
                dataset
                for project in user.project_set.all()
                for dataset in project.datasets.all()
            ]
        )
        # Fetch all necessary data at once before the loop
        dataset_ids = [dataset.id for dataset in possible_datasets]
        accesses = Access.objects.filter(
            Q(dataset_id__in=dataset_ids) & Q(status=StatusChoices.active)
        )

        for access in accesses:
            # Check if the dataset has an access that is about to expire
            if (
                access.grant_expires_on
                and access.grant_expires_on - day_offset == exec_date
            ):
                cls.notify(user, access, NotificationVerb.expire)

    @staticmethod
    def notify(user: "User", obj: "Access", verb: "NotificationVerb"):
        """
        Notifies concerning users about the entity.
        """
        dispatch_by_email = user.notification_setting.send_email
        dispatch_in_app = user.notification_setting.send_in_app

        msg = f"Access for {obj.dataset.title} of the user {obj.user or obj.contact} is expiring."
        on = obj.grant_expires_on

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


auditlog.register(Access)
