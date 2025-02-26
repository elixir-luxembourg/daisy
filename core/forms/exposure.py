from django import forms

from core.models import Exposure, Endpoint
from web.views.utils import get_rems_forms


class ExposureForm(forms.ModelForm):
    class Meta:
        model = Exposure
        fields = "__all__"
        exclude = [
            "created_by",
            "form_name",
            "is_deprecated",
            "deprecated_at",
            "deprecation_reason",
        ]

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        rems_forms_list = get_rems_forms()
        form_name_ids = []

        for rems_forms in rems_forms_list:
            form_name_ids.append(
                (
                    rems_forms["form/internal-name"]
                    + " -- "
                    + str(rems_forms["form/id"]),
                    rems_forms["form/id"],
                )
            )

        self.fields["form_id"] = forms.ChoiceField(
            label="Form",
            choices=[(i[1], i[0]) for i in form_name_ids],
            widget=forms.Select,
            help_text=self.fields["form_id"].help_text,
        )

        if not form_name_ids:
            self.fields["form_id"].help_text = (
                self.fields["form_id"].help_text
                + " Error: No forms retrieved form REMS"
            )

        exposure_list = Exposure.objects.filter(dataset=dataset, is_deprecated=False)
        endpoint_ids = exposure_list.values_list("endpoint", flat=True)
        self.fields["endpoint"].choices = [
            (e.id, e) for e in Endpoint.objects.exclude(id__in=endpoint_ids)
        ]

    field_order = ["endpoint", "form_id"]


class ExposureEditForm(forms.ModelForm):
    class Meta:
        model = Exposure
        fields = "__all__"
        exclude = [
            "created_by",
            "form_name",
            "is_deprecated",
            "deprecated_at",
            "deprecation_reason",
        ]

    field_order = ["endpoint", "form_id"]

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop("dataset", None)
        # current endpoint
        endpoint = kwargs.pop("endpoint", None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop("dataset")
        rems_forms_list = get_rems_forms()
        form_name_ids = []

        for rems_forms in rems_forms_list:
            form_name_ids.append(
                (
                    rems_forms["form/internal-name"]
                    + " -- "
                    + str(rems_forms["form/id"]),
                    rems_forms["form/id"],
                )
            )

        self.fields["form_id"] = forms.ChoiceField(
            label="Form",
            choices=[(i[1], i[0]) for i in form_name_ids],
            widget=forms.Select,
            help_text=self.fields["form_id"].help_text,
        )

        if not form_name_ids:
            self.fields["form_id"].help_text = (
                self.fields["form_id"].help_text
                + " Error: No forms retrieved form REMS"
            )

        exposure_list = Exposure.objects.filter(dataset=dataset)
        endpoint_ids = exposure_list.values_list("endpoint", flat=True)
        self.fields["endpoint"].choices = [
            (e.id, e) for e in Endpoint.objects.exclude(id__in=endpoint_ids)
        ] + [(endpoint.id, endpoint)]


class ExposureRemoveForm(forms.ModelForm):
    class Meta:
        model = Exposure
        fields = ["deprecation_reason"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["deprecation_reason"] = forms.CharField(
            widget=forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control",
                    "placeholder": "Please provide a reason for deprecating this exposure",
                }
            ),
            required=True,
            label="Deprecation Reason",
            help_text="Please provide a reason for deprecating this exposure.",
        )
