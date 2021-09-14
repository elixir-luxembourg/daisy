from django.forms import ModelForm, Textarea

from core.forms.input import SelectWithModal
from core.models import Cohort


class CohortForm(ModelForm):
    class Meta:
        model = Cohort
        fields = '__all__'
        widgets = {
            'comments': Textarea(attrs={'rows': 2, 'cols': 40}),
        }
        exclude = ('is_published',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['elu_accession'].disabled = True
        self.fields['owners'].widget = SelectWithModal(url_name='contact_add', entity_name='contact',
                                                          choices=self.fields['owners'].widget.choices,
                                                          allow_multiple_selected=True)

    field_order = [
        'title',
        'elu_accession',
        'owners',
        'institutes',
        'comments'
    ]


class CohortFormEdit(CohortForm):
    pass
