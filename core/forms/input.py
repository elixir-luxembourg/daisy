from django import forms
from django.forms import widgets
from os import path


class SelectWithModal(widgets.Select):
    template_name = "widgets/select.html"

    def __init__(self, url_name, entity_name, choices, allow_multiple_selected=False):
        super().__init__(choices=choices)
        self.entity_name = entity_name
        self.url_name = url_name
        self.allow_multiple_selected = allow_multiple_selected

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["url_name"] = self.url_name
        context["widget"]["entity_name"] = self.entity_name
        return context


class ContextObjectInput(forms.HiddenInput):
    def __init__(self, *args, **kwargs):
        self._initial = kwargs.pop("initial", {})
        self._content_type = self._initial.get("content_type", "")
        self._object_id = self._initial.get("object_id", "")
        super().__init__(*args, **kwargs)


class CustomClearableFileInput(forms.ClearableFileInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value is not None:
            value.name = path.basename(value.name)
        return context
