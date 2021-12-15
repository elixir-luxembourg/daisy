from django.db import migrations, models

from core import constants


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20211004_1610'),
    ]
    
    def correct_permissions_of_local_custodians(apps, schema_editor):
        Dataset = apps.get_model('core', 'Dataset')
        for dataset in Dataset.objects.all():
            for user in dataset.local_custodians.all():
                user.assign_permissions_to_dataset(dataset)

        Project = apps.get_model('core', 'Project')
        for project in Project.objects.all():
            for user in project.local_custodians.all():
                user.assign_permissions_to_dataset(project)


    def undo_correct_permissions_of_local_custodians(apps, schema_editor):
        Dataset = apps.get_model('core', 'Dataset')
        for dataset in Dataset.objects.all():
            for user in dataset.local_custodians.all():
                user._remove_perm(constants.Permissions.PROTECTED.value, user, dataset)

        Project = apps.get_model('core', 'Project')
        for project in Project.objects.all():
            for user in project.local_custodians.all():
                user._remove_perm(constants.Permissions.PROTECTED.value, user, project)
        

    operations = [

    # Correct permissions of local custodians
        migrations.RunPython(correct_permissions_of_local_custodians, undo_correct_permissions_of_local_custodians),

    ]
