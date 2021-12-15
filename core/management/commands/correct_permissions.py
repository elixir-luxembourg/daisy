import os

from django.conf import settings
from django.core.management import BaseCommand
from core import constants

from core.models import User, Dataset, Project
from core.constants import Permissions


class Command(BaseCommand):
    help = 'applies the changes to permissions system (local custodians will receive PRIVILLEGED permission to a resource)'

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--reverse',
            help='Reverse (undo the changes)',
            default=False
        )

    def _apply_fix(self):
        counter = 0
        ids = []
        for dataset in Dataset.objects.all():
            for user in dataset.local_custodians.all():
                if user.has_perm(Permissions.PROTECTED.value, dataset):
                    continue
                user._assign_perm(Permissions.PROTECTED.value, user, dataset)
                ids.append({'user_id': user.id, 'dataset_id': dataset.id})
                counter += 1
        print(f'Updated {counter} user entry(ies) for datasets'' local custodians: ', end='')
        print(ids)

        counter = 0
        ids = []
        for project in Project.objects.all():
            for user in project.local_custodians.all():
                if user.has_perm(Permissions.PROTECTED.value, project):
                    continue
                user._assign_perm(Permissions.PROTECTED.value, user, project)
                ids.append({'user_id': user.id, 'project_id': project.id})
                counter += 1
        print(f'Updated {counter} user entry(ies) for projects'' local custodians: ', end='')
        print(ids)

    def _reverse_fix(self):
        counter = 0
        ids = []
        for dataset in Dataset.objects.all():
            for user in dataset.local_custodians.all():
                if user.has_perm(Permissions.PROTECTED.value, dataset):
                    user._remove_perm(Permissions.PROTECTED.value, user, dataset)
                    ids.append({'user_id': user.id, 'dataset_id': dataset.id})
        print(f'Updated {counter} user entry(ies) for datasets'' local custodians: ', end='')
        print(ids)

        counter = 0
        ids = []
        for project in Project.objects.all():
            for user in project.local_custodians.all():
                if user.has_perm(Permissions.PROTECTED.value, project):
                    user._remove_perm(Permissions.PROTECTED.value, user, project)
                    ids.append({'user_id': user.id, 'project_id': project.id})
        print(f'Updated {counter} user entry(ies) for projects'' local custodians: ', end='')
        print(ids)

    def handle(self, *args, **options):
        try:
            if not(options.get('reverse')):
                self._apply_fix()
            else:
                self._reverse_fix()
        except Exception as e:
            msg = f'Something went wrong during correcting the permissions. Details: '
            self.stderr.write(self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))