from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse_lazy

from guardian.shortcuts import get_objects_for_user, get_users_with_perms, assign_perm, remove_perm

from core.constants import Permissions, Groups
from core.models import Dataset, Project
from core.forms import UserPermFormSet
from core.permissions.checker import AutoChecker

PAGINATE_BY = 5


def index(request, selection, pk):
    """
    Permission management page for projects or datasets.
    """

    # a selection have been made, we need to show it
    # and select rights classes
    if selection == 'project':
        klass = Project
    elif selection == 'dataset':
        klass = Dataset
    else:
        raise KeyError('Wrong selection')

    # get selected object (project or dataset)
    obj = klass.objects.get(pk=pk)

    checker = AutoChecker(request.user)
    # check if admin permission is there, otherwise forbid access
    if not checker.check(f'core.{Permissions.ADMIN.value}_{selection}', obj):
        raise PermissionDenied


    # get all users with permissions attached to the object (Project or Dataset)
    users_with_perms = get_users_with_perms(obj, attach_perms=True)

    # prepare the initial data to render in the form
    # remove request user and local custodians from it and treat them separately
    initial = []
    local_custodians = obj.local_custodians.all()
    local_vips = [u for u in local_custodians if u.is_part_of(Groups.VIP.value)]
    context = {
        'object': obj,
        'selection': selection,
        'edit_url': f"{selection}_edit",
        'local_custodians': local_custodians,
        'local_vips': local_vips,
        'pj_perms_const': list(map(lambda x: f"{x}_project", [p.value for p in Permissions])),
        'perms_const': list(Permissions),
    }
    # get inherited permissions from the parent project
    if klass == Dataset and obj.project is not None:
        context["inherited_permissions"] = get_users_with_perms(obj.project, attach_perms=True)
    for user, permissions in users_with_perms.items():
        if len(permissions) == 1 and 'view' in permissions[0]:
            continue
        # add user
        data = {
            'user': user,
        }
        # add permissions
        for perm in permissions:
            data[perm] = True
        initial.append(data)
    initial = sorted(initial, key=lambda x: x['user'].username)
    if request.method == 'GET':
        formset = UserPermFormSet(initial=initial, form_kwargs={"model": selection})

        context['formset'] = formset
        return render(request, 'permissions.html', context)

    if request.method != 'POST':
        # we accept only POST requests from here
        raise PermissionDenied

    formset = UserPermFormSet(request.POST, form_kwargs={"model": selection})
    if formset.is_valid():
        # assing/remove permission for each form in the formset
        for form in formset:
            data = form.cleaned_data
            if not data or 'user' not in data:
                continue
            user = data.pop('user')
            delete = data.pop('DELETE')

            # delete any permissions for the user if not a local custodian.
            if delete:
                if user in local_custodians:
                    messages.add_message(request, messages.ERROR, f"Cannot delete permission set for {user} - user is local custodian.")
                    continue
                for perm in Permissions:
                    remove_perm(f"{perm.value}_{selection}", user, obj)
                continue

            if user in local_vips:
                # don't do anything for local vips.
                continue
            elif user in local_custodians:
                # local custodians that are not VIP can be assigned or removed an ADMIN or PROTECTED perm. All other must stay the same
                for perm, value in data.items():
                    if value or data.get(f"{Permissions.ADMIN.value}_{selection}"):
                        assign_perm(perm, user, obj)
                    elif perm not in map(lambda x: f"{x}_{selection}",[Permissions.EDIT.value, Permissions.DELETE.value]):
                        remove_perm(perm, user, obj)
            else:
                # if no `if` has been executed, we loop over the permission and update them accordingly
                for perm, value in data.items():
                    if value or data.get(f"{Permissions.ADMIN.value}_{selection}"): # if admin perm is set, all other permssions must be true
                        assign_perm(perm, user, obj)
                    else:
                        remove_perm(perm, user, obj)

        return redirect(reverse_lazy(selection, kwargs={'pk': pk}))
    context['formset'] = formset
    return render(request, 'permissions.html', context)