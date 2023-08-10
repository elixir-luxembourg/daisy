from abc import abstractmethod
from json import loads
from json.decoder import JSONDecodeError

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import TextField
from django.utils.module_loading import import_string
from django.contrib.auth.hashers import make_password

COMPANY = getattr(settings, "COMPANY", "Company")


def validate_json(value):
    if len(value) == 0:
        return value

    try:
        loads(value)
        if (
            "{" not in value
        ):  # Very inaccurate, but should do the trick when the user tries to save e.g. '123'
            raise ValidationError(
                f"`scientific_metadata` field must be a valid JSON containing a dictionary!"
            )
        return value
    except JSONDecodeError as ex:
        msg = str(ex)
        raise ValidationError(
            f"`scientific_metadata` field must contain a valid JSON! ({msg})"
        )


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class CoreModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CoreTrackedModel(CoreModel):
    elu_accession = models.CharField(unique=True, blank=True, null=True, max_length=20)

    scientific_metadata = models.TextField(
        default="{}",
        blank=True,
        null=True,
        verbose_name="Additional scientific metadata (in JSON format)",
        validators=[validate_json],  # This will work in ModelForm only
    )

    class Meta:
        abstract = True

    @abstractmethod
    def is_published(self):
        pass

    @abstractmethod
    def publish(self):
        pass

    def clean(self):
        cleaned_data = super().clean()
        validate_json(self.scientific_metadata)
        return cleaned_data

    def save(self, *args, **kwargs):
        self.clean()  # Ensure the validator on metadata field is triggered
        super().save(*args, **kwargs)


class CoreTrackedDBModel(CoreTrackedModel):
    _is_published = models.BooleanField(
        default=False, blank=False, verbose_name="Is published?"
    )

    class Meta:
        abstract = True

    def publish(self, save=True):
        generate_id_function_path = getattr(settings, "IDSERVICE_FUNCTION")
        generate_id_function = import_string(generate_id_function_path)
        if not self.is_published:
            self.is_published = True
            if not self.elu_accession:
                self.elu_accession = generate_id_function(self)
        if save:
            self.save(update_fields=["_is_published", "elu_accession"])

    @property
    def is_published(self):
        # Getter method
        return self._is_published

    @is_published.setter
    def is_published(self, value):
        # Setter method
        self._is_published = value


class TextFieldWithInputWidget(TextField):
    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {"max_length": self.max_length}
        if not self.choices:
            defaults["widget"] = forms.TextInput
        defaults.update(kwargs)
        return super().formfield(**defaults)


class HashedField(models.CharField):
    """
    A custom field that will store a hash of the provided value.
    """

    description = "Keeps the hash of the string in the DB"

    def pre_save(self, model_instance, add):
        """
        This function is called when the value is about to be saved to the DB. We hash the value and return it.
        """
        value = getattr(model_instance, self.attname)
        return make_password(value, salt=settings.SECRET_KEY)
