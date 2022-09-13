from django.core.management import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Applies changes to permissions system (all local custodians will receive permission to a resource)'

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--reverse',
            help='Reverse (undo the changes)',
            action='store_true'
        ), 
        parser.add_argument(
            '-p',
            '--permission',
            help='PERMISSION to be set. Possible values: view (default), protected, delete, edit, admin',
            default='view'
        )

    def _apply_fix(self, permission):
        classes_to_update = ['Dataset', 'Project']
        print(f'Setting {permission} permission to all local custodians on models: {classes_to_update}.')
        for class_to_update in classes_to_update:
            model_to_update = apps.get_model('core', class_to_update)
            ids = []
            counter = 0
            for obj in model_to_update.objects.all():
                for user_obj in obj.local_custodians.all():
                    if user_obj.has_perm(permission, obj):
                       continue
                    user_obj._assign_perm(permission, user_obj, obj)
                    ids.append({'user_id': user_obj.id, 'obj_id': obj.id})
                    counter += 1
            print(f'Updated {counter} user entry(ies) for {class_to_update}'' local custodians: ', end='')
            print(ids)

    def _reverse_fix(self, permission):
        classes_to_update = ['Dataset', 'Project']
        print(f'Removing {permission} permission to all local custodians on models: {classes_to_update}.')
        for class_to_update in classes_to_update:
            model_to_update = apps.get_model('core', class_to_update)
            ids = []
            counter = 0
            for obj in model_to_update.objects.all():
                for user_obj in obj.local_custodians.all():
                    if user_obj.has_perm(permission, obj):
                        user_obj._remove_perm(permission, user_obj, obj)
                        ids.append({'user_id': user_obj.id, 'obj_id': obj.id})
                        counter += 1
            print(f'Updated {counter} user entry(ies) for {class_to_update}'' local custodians: ', end='')
            print(ids)

    def handle(self, *args, **options):
        try:
            permission = options.get('permission')
            if not(options.get('reverse')):
                self._apply_fix(permission)
            else:
                self._reverse_fix(permission)
        except Exception as e:
            msg = f'Something went wrong during correcting the permissions. Details: '
            self.stderr.write(self.style.ERROR(msg))
            self.stderr.write(self.style.ERROR(str(e)))