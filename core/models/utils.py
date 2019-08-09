from django import forms
from django.conf import settings
from django.db import models
from django.db.models import TextField
from django.urls import reverse, NoReverseMatch

COMPANY = getattr(settings, "COMPANY", 'Company')


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class CoreModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_audit_url(self):
        try:
            return reverse('audit', kwargs={
                'pk': self.pk,
                'model_name': self.__class__.__name__.lower()
            })
        except NoReverseMatch:
            pass
    
    def get_detail_url(self):
        try:
            return reverse(self.__class__.__name__.lower(), kwargs={
                'pk': self.pk,
            })
        except NoReverseMatch:
            pass

class CoreTrackedModel(CoreModel):
    is_published = models.BooleanField(default=False,
                                       blank=False,
                                       verbose_name='Is published?')
    elu_accession = models.CharField(default='-', blank=True, null=False, max_length=20)

    class Meta:
        abstract = True


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
