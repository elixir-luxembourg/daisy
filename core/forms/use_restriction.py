from django.core.exceptions import ValidationError
from django.forms import CharField, ModelForm, Select

from core.models import UseRestriction, RestrictionClass


class UseRestrictionForm(ModelForm):
    """
    Form for data use restrictions. It is intended to be included in a formset.
    """

    class Meta:
        model = UseRestriction
        fields = ('restriction_class', 'notes')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        class_choices = [(None, "-----------------------")]
        class_choices.extend([(d.code, d.name) for d in RestrictionClass.objects.all()])
        self.fields['restriction_class'] = CharField(label='Category', help_text= 'Select the category of restrictions. These are \'GA4GH Consent Codes\'', required=True, widget=Select(choices=class_choices, attrs={'class': 'dummy-select'}))
        self.fields['notes'].widget.attrs['cols'] = '70'
        self.fields['notes'].widget.attrs['rows'] = '1'


    def clean(self):
        cleaned_data = super().clean()
        restriction_class = cleaned_data.get('restriction_class')
        notes = cleaned_data.get('notes')
        if not restriction_class and notes:
            self.add_error('restriction_class', 'Please select a valid restriction class')
        return self.cleaned_data


    def is_empty(self):
        cleaned_data = super().clean()
        restriction_class = cleaned_data.get('restriction_class')
        notes = cleaned_data.get('notes')
        return not restriction_class and not notes