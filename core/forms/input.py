from django import forms
from django.forms import widgets
from django.template import loader
from os import path

class SelectWithModal(widgets.Select):
    template_name = 'widgets/select.html'

    def __init__(self, url_name, entity_name, choices, allow_multiple_selected=False):
        super().__init__(choices=choices)
        self.entity_name = entity_name
        self.url_name = url_name
        self.allow_multiple_selected = allow_multiple_selected

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['url_name'] = self.url_name
        context['widget']['entity_name'] = self.entity_name
        return context


# class DropzoneInput(forms.FileInput):
#     template_name = "dropzone/dropzone.html"
#
#     class Media:
#         js = ("js/dropzone.js", "js/document-dz.js")
#         # css = {"all": ("css/dropzone.css",)}
#
#     def _to_dropzone_file(self, file):
#         """
#         Convert Django file element to a dropzone file.
#         """
#         return {"id": file.pk, "name": file.shortname, "size": file.size}
#
#     def _get_files(self):
#         """
#         Get the files from the doccument
#         """
#         files = []
#         for f in self._files:
#             files.append(self._to_dropzone_file(f))
#         return files
#
#     def __init__(self, *args, **kwargs):
#         # set default
#         self._dropzone = kwargs.pop('dropzone', {})
#         self._selector = self._dropzone.get('selector', '.dropzone')
#         self._files = self._dropzone.get('datafiles', [])
#         self._document_edit = self._dropzone.get('document_edit', {})
#         self._config = self._dropzone.get('config', {
#             "maxFilesize": 2,  # 2MB
#             "paramName": "content",
#         })
#         super().__init__(*args, **kwargs)
#
#     def render(self, name, value, attrs=None):
#         if value is None:
#             value = ""
#
#         ctx = {
#             "selector": self._selector,
#             "config": self._config,
#             "files": [],
#             "document_edit": self._dropzone.get('document_edit'),
#             "download_url": self._dropzone.get('download_url'),
#             "delete_url": self._dropzone.get('delete_url'),
#         }
#         if self._config:
#             ctx["url"] = self._config.get('url', ''),
#         if self._files:
#             ctx["files"] = self._get_files()
#         tmpl = loader.get_template(self.template_name)
#         return tmpl.render(ctx)
#

class ContextObjectInput(forms.HiddenInput):
    def __init__(self, *args, **kwargs):
        self._initial = kwargs.pop('initial', {})
        self._content_type = self._initial.get('content_type','')
        self._object_id = self._initial.get('object_id', '')
        super().__init__(*args, **kwargs)


class CustomClearableFileInput(forms.ClearableFileInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value is not None:
            value.name = path.basename(value.name)
        return context