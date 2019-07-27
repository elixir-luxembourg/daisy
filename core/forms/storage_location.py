from django import forms
from core.models.storage_location import DataLocation


class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = '__all__'
        exclude = []

    def __init__(self, *args, **kwargs):
        dataset = kwargs.pop('dataset', None)
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in dataset.data_declarations.all()]

    field_order = [
        'category',
        'backend',
        'data_declarations',
        'datatypes',
        'location_description'
    ]

class StorageLocationEditForm(forms.ModelForm):
    class Meta:
        model = DataLocation
        fields = '__all__'
        exclude = []

    field_order = [
        'category',
        'backend',
        'data_declarations',
        'datatypes',
        'location_description'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't allow editing dataset
        self.fields.pop('dataset')
        self.fields['data_declarations'].choices = [(d.id, d.title) for d in kwargs['instance'].dataset.data_declarations.all()]


    # class PickStorageLocationForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['data_file'] = forms.ChoiceField(choices=[(d.id, str(d)) for d in DataLocation.objects.all()])
#

# def dataLocationFormFactory(*args, **kwargs):
#     model_form_class = DataLocation
#     initial = kwargs.pop('initial', {})
#     backend = kwargs.pop('backend', None)
#     if backend is not None:
#         model_form_class = backend.get_location_class()
#         initial['backend'] = backend
#
#     class DataLocationForm(forms.ModelForm):
#
#         class Meta:
#             model = model_form_class
#             fields = '__all__'
#             exclude = []
#
#         backend = forms.ModelChoiceField(
#             queryset=StorageResource.objects.all(),
#             widget=forms.Select(attrs={'id': 'storage-backend'})
#         )
#
#         def __init__(self, *args, **kwargs):
#             self.dataset = kwargs.pop('dataset', None)
#             super().__init__(*args, **kwargs)
#             if self.dataset:
#                 self.fields.pop('dataset')
#
#     return DataLocationForm(*args, **kwargs, initial=initial)

    # def get_form_class(self):
    #     print('get form class')
    #     if not self._request or not 'backend' in self._request.GET:
    #         return super().get_form_class()

    # def get_form(self, request, obj=None, **kwargs):
    #     print('get_form', request.GET)
    #     if obj is None:
    #         Model = DataLocation.SUBCLASS(request.GET.get('storage_resource'))
    #     else:
    #         Model = obj.__class__

    #     # When we change the selected storage resource in the create form, we want to reload the page.
    #     RELOAD_PAGE = "window.location.search='?storage_resource=' + this.value"
    #     # We should also grab all existing field values, and pass them as query string values.

    #     class ModelForm(forms.ModelForm):
    #         if not obj:
    #             storage_resource = forms.ChoiceField(
    #                 choices=[('', 'Please select...')] + DataLocation.SUBCLASS_CHOICES,
    #                 widget=forms.Select(attrs={'onchange': RELOAD_PAGE})
    #             )

    #         class Meta:
    #             model = Model
    #             exclude = ()

    #     return ModelForm

    # def get_fields(self, request, obj=None):
    #     # We want storage_resource to be the first field.
    #     fields = super().get_fields(request, obj)
    #     if 'storage_resource' in fields:
    #         fields.remove('storage_resource')
    #         fields = ['storage_resource'] + fields
    #     return fields

    # def get_urls(self):
    #     # We want to install named urls that match the subclass ones, but bounce to the relevant
    #     # superclass ones (since they should be able to handle rendering the correct form).
    #     urls = super().get_urls()
    #     existing = '{}_{}_'.format(self.model._meta.app_label, self.model._meta.model_name)
    #     subclass_urls = []
    #     for name, model in DataLocation.SUBCLASS_OBJECT_CHOICES.items():
    #         opts = model._meta
    #         replace = '{}_{}_'.format(opts.app_label, opts.model_name)
    #         subclass_urls.extend([
    #             url(pattern.regex.pattern, pattern.callback, name=pattern.name.replace(existing, replace))
    #             for pattern in urls if pattern.name
    #         ])
    #     return urls + subclass_urls
