from django.forms import CharField, ModelForm, Select

from core.models import UseCondition, ConditionClass
from core.models.use_condition import USE_CONDITION_CHOICES


class UseConditionForm(ModelForm):
    """
    Form for data use conditions. It is intended to be included in a formset.
    """

    class Meta:
        model = UseCondition
        fields = (
            "use_condition_rule",
            "condition_class",
            "notes",
            "use_class_note",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        class_choices = [(None, "-----------------------")]
        class_choices.extend([(d.code, d.name) for d in ConditionClass.objects.all()])
        self.fields["condition_class"] = CharField(
            label="Use category",
            help_text="Select the category of conditions. These are 'GA4GH Consent Codes'",
            required=False,
            widget=Select(choices=class_choices, attrs={"class": "dummy-select"}),
        )
        self.fields["notes"].widget.attrs["cols"] = "70"
        self.fields["notes"].widget.attrs["rows"] = "5"
        self.fields["use_condition_rule"] = CharField(
            label="Use Condition Rule",
            help_text="Does the rule constrain or forbid?",
            required=True,
            initial=USE_CONDITION_CHOICES.PROHIBITION,
            widget=Select(
                choices=USE_CONDITION_CHOICES, attrs={"class": "dummy-select"}
            ),
        )
        self.fields["use_class_note"].widget.attrs["cols"] = "70"
        self.fields["use_class_note"].widget.attrs["rows"] = "3"

    def clean(self):
        cleaned_data = super().clean()
        condition_class = cleaned_data.get("condition_class")
        notes = cleaned_data.get("notes")
        if not condition_class:
            self.add_error("condition_class", "Please select a valid condition class")
        return self.cleaned_data

    def is_empty(self):
        cleaned_data = super().clean()
        condition_class = cleaned_data.get("condition_class")
        notes = cleaned_data.get("notes")
        use_class_note = cleaned_data.get("use_class_note")
        # use_condition_rule = cleaned_data.get('use_condition_rule')
        return (
            not condition_class and not notes and not use_class_note
        )  # Warning: omitting `use_condition_rule!`
