from django.db.models.base import ModelBase

from .utils import CoreModel, TextFieldWithInputWidget


class MetaGDRPRole(ModelBase):
    def __getitem__(cls, item):
        if item not in cls.all_roles:
            role = cls.objects.filter(name=item).get()
            cls.all_roles[item] = role
        return cls.all_roles[item]


class GDPRRole(CoreModel, metaclass=MetaGDRPRole):
    """
    Objects of this class represent the different GDPR Roles
    """

    class Meta:
        app_label = "core"
        get_latest_by = "added"
        ordering = ["name"]

    name = TextFieldWithInputWidget(blank=False)
    display_name = TextFieldWithInputWidget(blank=False)

    def __str__(self):
        return self.display_name

    all_roles = {}
