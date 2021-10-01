from django import forms
from django.conf import settings
from django.db import models
from django.db.models import TextField
from django.utils.module_loading import import_string


COMPANY = getattr(settings, "COMPANY", 'Company')

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class CoreModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CoreTrackedModel(CoreModel):
    elu_accession = models.CharField(
        unique=True,
        blank=True,
        null=True,
        max_length=20)
    
    is_published = models.BooleanField(
        default=False,
        blank=False,
        verbose_name='Is published?')

    scientific_metadata = models.TextField(
        default='{}',
        blank=False,
        null=False,
        verbose_name='Additional scientific metadata (in JSON format)'
    )
    class Meta:
        abstract = True

    def publish(self, save=True):
        generate_id_function_path = getattr(settings, 'IDSERVICE_FUNCTION')
        generate_id_function = import_string(generate_id_function_path)
        if not self.is_published:
            self.is_published = True
            if not self.elu_accession:
                self.elu_accession = generate_id_function(self)
        if save:
            self.save(update_fields=['is_published', 'elu_accession'])


class TextFieldWithInputWidget(TextField):

    def formfield(self, **kwargs):
        # Passing max_length to forms.CharField means that the value's length
        # will be validated twice. This is considered acceptable since we want
        # the value in the form field (to pass into widget for example).
        defaults = {'max_length': self.max_length}
        if not self.choices:
            defaults['widget'] = forms.TextInput
        defaults.update(kwargs)
        return super().formfield(**defaults)
