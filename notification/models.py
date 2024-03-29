"""
model classes based on http://activitystrea.ms/specs/json/1.0/

Notification class does not have any target at the moment.
"""
from datetime import datetime

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from django.conf import settings

from enumchoicefield import EnumChoiceField, ChoiceEnum


class NotificationStyle(ChoiceEnum):
    never = "Never"
    every_time = "Every time"
    once_per_day = "Once per day"
    once_per_week = "Once per week"
    once_per_month = "Once per month"


class NotificationVerb(ChoiceEnum):
    expire = "expire"
    start = "start"
    end = "end"
    embargo_start = "embargo_start"
    embargo_end = "embargo_end"


class NotificationSetting(models.Model):
    class Meta:
        app_label = "notification"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="notification_setting",
        on_delete=models.CASCADE,
    )
    send_email = models.BooleanField(
        default=False,
        help_text="Notifications will be send directly to your email. See your [profile page] for more detail.",
    )
    send_in_app = models.BooleanField(
        default=True,
        help_text="Notification will be displayed in DAISY interface",
    )
    notification_offset = models.PositiveSmallIntegerField(
        default=90,
        verbose_name="Notification time",
        help_text="Define how many days before the actual event you want to receive the notification",
    )

    def __str__(self):
        return f"{self.user}: {self.notification_offset} days"


class NotificationQuerySet(models.QuerySet):
    def ordered(self):
        return self.order_by("-time")


class NotificationManager(models.Manager):
    def get_queryset(self):
        return NotificationQuerySet(self.model, using=self._db)

    def ordered(self):
        return self.get_queryset().ordered()


class Notification(models.Model):
    class Meta:
        app_label = "notification"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE
    )
    verb = EnumChoiceField(NotificationVerb)
    on = models.DateTimeField(null=True, blank=True, default=None)

    dispatch_in_app = models.BooleanField(default=True)
    dispatch_by_email = models.BooleanField(default=False)
    dismissed = models.BooleanField(default=False)
    processing_date = models.DateField(default=None, null=True, blank=True)
    message = models.TextField(default="")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    time = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = NotificationManager()

    def get_absolute_url(self):
        model_class = self.content_type.model_class()
        if hasattr(model_class, "get_absolute_url"):
            return model_class.objects.get(pk=self.object_id).get_absolute_url()
        return None

    def get_full_url(self):
        """
        Get the full url of the content_object (with the server scheme and url).
        """
        return "%s://%s%s" % (
            settings.SERVER_SCHEME,
            settings.SERVER_URL,
            self.get_absolute_url(),
        )

    @property
    def event_time(self):
        return datetime.now()

    def to_json(self):
        user_json = (
            self.recipient.to_json()
            if hasattr(self.recipient, "to_json")
            else {"id": self.recipient.id, "name": self.recipient.get_full_name()}
        )
        return {
            "id": self.id,
            "recipient": user_json,
            "verb": self.verb.value,
            "on": self.on,
            "time": self.time,
            "sentInApp": self.dispatch_in_app,
            "sentByEmail": self.dispatch_by_email,
            "dismissed": self.dismissed,
            "message": self.message,
            "objectType": self.content_type.model,
            "objectClass": self.content_type.name,
            "objectDisplayName": self.content_object.display_name()
            if hasattr(self.content_object, "display_name")
            else self.content_object.__str__(),
            "objectUrl": self.get_absolute_url() or "",
        }

    def __str__(self):
        return f"N: {self.recipient} {self.verb} {self.object_id} {self.time}"
