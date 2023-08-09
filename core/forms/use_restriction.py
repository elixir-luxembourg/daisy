from django.core.exceptions import ValidationError
from django.forms import CharField, ModelForm, Select

from core.models import UseRestriction, RestrictionClass
from core.models.use_restriction import USE_RESTRICTION_CHOICES


class UseRestrictionForm(ModelForm):
    """
    Form for data use restrictions. It is intended to be included in a formset.
    """

    class Meta:
        model = UseRestriction
        fields = (
            "use_restriction_rule",
            "restriction_class",
            "notes",
            "use_class_note",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        class_choices = [(None, "-----------------------")]
        class_choices.extend([(d.code, d.name) for d in RestrictionClass.objects.all()])
        self.fields["restriction_class"] = CharField(
            label="Use category",
            help_text="Select the category of restrictions. These are 'GA4GH Consent Codes'",
            required=False,
            widget=Select(choices=class_choices, attrs={"class": "dummy-select"}),
        )
        self.fields["notes"].widget.attrs["cols"] = "70"
        self.fields["notes"].widget.attrs["rows"] = "5"
        self.fields["use_restriction_rule"] = CharField(
            label="Use Restriction Rule",
            help_text="Does the rule constraints or forbids?",
            required=True,
            initial=USE_RESTRICTION_CHOICES.PROHIBITION,
            widget=Select(
                choices=USE_RESTRICTION_CHOICES, attrs={"class": "dummy-select"}
            ),
        )
        self.fields["use_class_note"].widget.attrs["cols"] = "70"
        self.fields["use_class_note"].widget.attrs["rows"] = "3"

    def clean(self):
        cleaned_data = super().clean()
        restriction_class = cleaned_data.get("restriction_class")
        notes = cleaned_data.get("notes")
        if not restriction_class:
            self.add_error(
                "restriction_class", "Please select a valid restriction class"
            )
        return self.cleaned_data

    def is_empty(self):
        cleaned_data = super().clean()
        restriction_class = cleaned_data.get("restriction_class")
        notes = cleaned_data.get("notes")
        use_class_note = cleaned_data.get("use_class_note")
        # use_restriction_rule = cleaned_data.get('use_restriction_rule')
        return (
            not restriction_class and not notes and not use_class_note
        )  # Warning: omitting `use_restriction_rule!`
