"""
Module that handle permission management.
"""
import logging

from abc import ABCMeta, abstractmethod

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.functional import wraps
from guardian.core import ObjectPermissionChecker
from guardian.mixins import PermissionRequiredMixin

from core import constants
from core.exceptions import DaisyError

logger = logging.getLogger('daisy.permissions')


class AbstractChecker(metaclass=ABCMeta):
    """
    Abstract Base Class to check objects permission in  DAISY.
    """

    def __init__(self, user_or_group, checker=None):
        self.user_or_group = user_or_group
        self.checker = checker
        if checker is None:
            self.checker = ObjectPermissionChecker(user_or_group)

    def _set_perm(self, perm):
        # transform Permission enum to it's str value
        if isinstance(perm, constants.Permissions):
            self._perm = perm
            perm = 'core.%s' % perm.value
        return perm

    def check(self, perm, obj, **kwargs):
        perm = self._set_perm(perm)
        # check global perm first then check on object
        return self.user_or_group.has_perm(perm) or self._check(perm, obj, **kwargs)

    @abstractmethod
    def _check(self, perm, obj, **kwargs):
        """
        Perform the permission check
        """
        pass


class ProjectChecker(AbstractChecker):
    """
    Check permissions on project.
    """

    def _check(self, perm, obj, **kwargs):
        return self.checker.has_perm(perm, obj)


class DatasetChecker(AbstractChecker):
    """
    Check permissions on dataset.
    """

    def _check(self, perm, obj, **kwargs):
        hasperm = self.checker.has_perm(perm, obj)
        logger.debug(f'[DatasetChecker _check] Checking permission "{perm}" on: "{obj}": {hasperm}.')
        if hasperm:
            return True
        nofollow = kwargs.pop('nofollow', False)
        if nofollow:
            return False
        try:
            project = obj.project
            if project is None:
                return False
            return ProjectChecker(self.user_or_group, checker=self.checker).check(perm, project, **kwargs)
        except ObjectDoesNotExist:
            return False


class DataDeclarationChecker(AbstractChecker):
    """ Check permissions on data declaration"""

    def _check(self, perm, obj, **kwargs):
        return DatasetChecker(self.user_or_group, checker=self.checker).check(perm, obj.dataset, **kwargs)


class ContractChecker(AbstractChecker):
    """
    Check permission on contract.
    """

    def _check(self, perm, obj, **kwargs):
        if self.checker.has_perm(perm, obj):
            return True
        no_follow = kwargs.pop('nofollow', False)
        if no_follow:
            return False
        if obj.project is None:
            return False
        return ProjectChecker(self.user_or_group, checker=self.checker).check(perm, obj.project, **kwargs)


class DocumentChecker(AbstractChecker):
    """
    Check permission on document.
    Document are protected entities
    Only some defined group can see them can see them (this check is made on the Abstract Class)
    And only the people who have PROTECTED rights on the project can see them.
    """

    def check(self, perm, obj, **kwargs):
        perm = self._set_perm(perm)
        # does not check global perm for document.
        return self._check(perm, obj, **kwargs)

    def _check(self, perm, obj, **kwargs):
        """
        Check the permission on the underlying content_object
        """
        if self.checker.has_perm(perm, obj):
            return True
        nofollow = kwargs.pop('nofollow', False)
        if nofollow:
            return False
        if obj.content_type.name == 'project':
            return ProjectChecker(self.user_or_group, checker=self.checker).check(
                self._perm,
                obj.content_object,
                **kwargs
            )
        else:
            return ContractChecker(self.user_or_group, checker=self.checker).check(
                self._perm,
                obj.content_object,
                **kwargs
            )


class AutoChecker(AbstractChecker):
    """
    Check permission on given object. Object must be instance on a key in the __mapping attribute.
    """

    __mapping = {
        'Dataset': DatasetChecker,
        'Project': ProjectChecker,
        'Contract': ContractChecker,
        'Document': DocumentChecker,
        'DataDeclaration': DataDeclarationChecker
    }

    # override default check method
    def check(self, perm, obj, **kwargs):
        return self._check(perm, obj, **kwargs)

    def _check(self, perm, obj, **kwargs):
        """
        Check the permission on the object.
        Automatically determines which permission class to use.
        """
        value = self.__mapping[obj.__class__.__name__](self.user_or_group, checker=self.checker).check(perm, obj,
                                                                                                      **kwargs)
        logger.debug(f'[AutoChecker] Checking permission "{perm}" on {obj.__class__.__name__}: "{obj}" for "{self.user_or_group}": {value}.')
        return value


def permission_required(perm, lookup_variables):
    """
    Simplified version of https://github.com/django-guardian/django-guardian/blob/master/guardian/decorators.py
    """

    def dec(view_func):
        def wrapper(request, *args, **kwargs):
            # get object
            model, lookups = lookup_variables[0], lookup_variables[1:]
            if len(lookups) % 2 != 0:
                raise DaisyError("Lookup variables must be provided as pairs of lookup_string and view_arg")
            lookup_dict = {}
            for lookup, view_arg in zip(lookups[::2], lookups[1::2]):
                if view_arg not in kwargs:
                    raise DaisyError("Argument '%s' was not passed into view function" % view_arg)
                lookup_dict[lookup] = kwargs[view_arg]
            obj = get_object_or_404(model, **lookup_dict)
            # check permission
            if not AutoChecker(request.user).check(perm, obj):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wraps(view_func)(wrapper)

    return dec


def permission_required_from_content_type(perm, content_type_attr, object_id_attr, from_post=False):
    """
    Simplified version of https://github.com/django-guardian/django-guardian/blob/master/guardian/decorators.py
    """

    def dec(view_func):
        def wrapper(request, *args, **kwargs):
            obj = None
            # get parameters
            if from_post:
                content_type_pk = request.POST.get(content_type_attr)
                object_id = request.POST.get(object_id_attr)
            else:
                if content_type_attr not in kwargs:
                    raise DaisyError("Argument '%s' was not passed into view function" % content_type_attr)
                if object_id_attr not in kwargs:
                    raise DaisyError("Argument '%s' was not passed into view function" % object_id_attr)
                content_type_pk = kwargs.get(content_type_attr)
                object_id = kwargs.get(object_id_attr)
            # get content type object
            try:
                content_type = ContentType.objects.get_for_id(content_type_pk)
                obj = content_type.get_object_for_this_type(pk=object_id)
            except ObjectDoesNotExist:
                raise Http404
            # check permission
            if not AutoChecker(request.user).check(perm, obj):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wraps(view_func)(wrapper)

    return dec


class CheckerMixin(PermissionRequiredMixin):
    """
    A view mixin that verifies if the current logged in user has the specified permission
    using our checker methods.
    """

    def check_permissions(self, request):
        """
        Checks if *request.user* has all permissions returned by
        *get_required_permissions* method.

        :param request: Original request.
        """
        obj = self.get_permission_object()
        has_permission = AutoChecker(request.user).check(self.permission_required, obj)
        if not has_permission:
            raise PermissionDenied()
        return None

