from django.db import migrations, connection, DataError
from core.permissions.mapping import PERMISSION_MAPPING, GROUP_PERMISSIONS

# BEFORE UPGRADE:
# Django default permissions can be safely upgraded?
# - PROTECTED is given on documents -> Needs to be skipped (protected only attributed to projects and contracts atm)
#
def is_test_environment(db_cursor):
    db_cursor.execute(
        "SELECT id from django_content_type "
        "WHERE app_label='core'"
    )

    return not db_cursor.fetchall()


def rollback_new_permissions(apps, schema_editor):
    # Even if we rollback, we do not want to delete the new permissions from the database
    pass


def rollback_group_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions given to groups
        cursor.execute(
            "DELETE from auth_group_permissions "
            "WHERE auth_group_permissions.permission_id IN ("
            "   SELECT auth_permission.id FROM auth_permission "
            "   INNER JOIN django_content_type ON auth_permission.content_type_id = django_content_type.id "
            "   WHERE auth_permission.codename LIKE '%\_%' AND django_content_type.app_label = 'core'"
            ")"
        )


def rollback_django_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be put back in permission attributions
        cursor.execute(
            "SELECT auth_permission.id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model FROM auth_permission "
            "INNER JOIN django_content_type on auth_permission.content_type_id = django_content_type.id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' AND django_content_type.app_label = 'core'"
        )
        results = cursor.fetchall()

        if results:
            for id, codename, content_type_id, model_name in results:
                new_codename = f"{codename if codename != 'edit' else 'change'}_{model_name}"

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (new_codename, content_type_id)
                )
                new_permission_id = cursor.fetchall()
                # New permission not found. This is problematic if the target model is contract, dataset or project...
                # ... and if the permission is a default one.
                if not new_permission_id:
                    if codename in ['admin', 'protected'] \
                            and model_name not in ['contract', 'dataset', 'project']:
                        continue
                    else:
                        raise ValueError(f"No permission was found for codename={new_codename} and content_type_id={content_type_id}")
                else:
                    assert len(new_permission_id) == 1
                    new_permission_id, = new_permission_id[0]
                    print(f"Replacing new permission {new_codename} (id={new_permission_id}) by {codename} (id={id}, target={model_name})")
                    cursor.execute(
                        "UPDATE core_user_user_permissions "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s ",
                        (id, new_permission_id)
                    )

        else:
            raise DataError("Old permissions were removed from the database. Impossible to roll back")


def rollback_guardian_userobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model FROM guardian_userobjectpermission "
            "INNER JOIN django_content_type on guardian_userobjectpermission.content_type_id = django_content_type.id "
            "INNER JOIN auth_permission on auth_permission.id = guardian_userobjectpermission.permission_id "
            "WHERE auth_permission.codename LIKE '%\_%' AND django_content_type.app_label = 'core'"
            "GROUP BY permission_id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model"
        )
        results = cursor.fetchall()
        if results:
            for id, codename, content_type_id, model_name in results:
                previous_codename = codename.split('_')[0]
                previous_codename = 'edit' if previous_codename == 'change' else previous_codename

                # Finding the old permission id
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (previous_codename, content_type_id)
                )
                old_permission_id = cursor.fetchall()
                if not old_permission_id:
                    raise ValueError(f"No permission was found for codename={previous_codename} and content_type_id={content_type_id}")
                else:
                    assert len(old_permission_id) == 1
                    old_permission_id, = old_permission_id[0]
                    print(f"Replacing new permission {codename} (id={id}, target={model_name}) by {previous_codename} (id={old_permission_id})")
                    cursor.execute(
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (old_permission_id, id, content_type_id)
                    )
        else:
            print("No new permission was found on contracts. Nothing to roll back.")


def rollback_core_datasetuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be put back in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_datasetuserobjectpermission "
            "INNER JOIN auth_permission on auth_permission.id = core_datasetuserobjectpermission.permission_id "
            "WHERE auth_permission.codename LIKE '%\_%' "
            "GROUP BY permission_id, auth_permission.codename"
        )

        results = cursor.fetchall()
        if results:
            model_name = 'dataset'
            cursor.execute(
                "SELECT id from django_content_type "
                "WHERE app_label='core' and model = 'dataset'"
            )
            content_type_id = cursor.fetchone()[0]
            for id, codename in results:
                previous_codename = codename.split('_')[0]
                previous_codename = 'edit' if previous_codename == 'change' else previous_codename

                # Finding the old permission id
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (previous_codename, content_type_id)
                )
                old_permission_id = cursor.fetchall()
                if not old_permission_id:
                    raise ValueError(f"No permission was found for codename={previous_codename} and content_type_id={content_type_id}")
                else:
                    assert len(old_permission_id) == 1
                    old_permission_id, = old_permission_id[0]
                    print(f"Replacing new permission {codename} (id={id}, target={model_name}) by {previous_codename} (id={old_permission_id})")
                    cursor.execute(
                        "UPDATE core_datasetuserobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s",
                        (old_permission_id, id)
                    )
        else:
            print("No new permission was found on datasets. Nothing to roll back.")


def rollback_core_projectuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be put back in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_projectuserobjectpermission "
            "INNER JOIN auth_permission on auth_permission.id = core_projectuserobjectpermission.permission_id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' "
            "GROUP BY permission_id, auth_permission.codename"
        )

        results = cursor.fetchall()
        if results:
            model_name = 'project'
            cursor.execute(
                "SELECT id from django_content_type "
                "WHERE app_label='core' and model = 'project'"
            )
            content_type_id = cursor.fetchone()[0]
            for id, codename in results:
                previous_codename = codename.split('_')[0]
                previous_codename = 'edit' if previous_codename == 'change' else previous_codename

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (previous_codename, content_type_id)
                )
                old_permission_id = cursor.fetchall()
                if not old_permission_id:
                    raise ValueError(f"No permission was found for codename={previous_codename} and content_type_id={content_type_id}")
                else:
                    assert len(old_permission_id) == 1
                    old_permission_id, = old_permission_id[0]
                    print(f"Replacing old permission {codename} (id={id}, target={model_name}) by {previous_codename} (id={old_permission_id})")
                    cursor.execute(
                        "UPDATE core_projectuserobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s",
                        (old_permission_id, id)
                    )
        else:
            print("No new permission was found on projects. Nothing to roll back.")


def create_new_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return

        for target, permissions_list in PERMISSION_MAPPING.items():
            for permission_item in permissions_list:
                codename, description = permission_item
                print(f"Searching for {codename} permission")
                cursor.execute(
                    "SELECT auth_permission.id FROM auth_permission "
                    "INNER JOIN django_content_type on auth_permission.content_type_id = django_content_type.id "
                    "WHERE auth_permission.codename=%s AND django_content_type.app_label='core' AND django_content_type.model=%s",
                    [codename, target.lower()]
                )

                results = cursor.fetchall()
                if not results:
                    # Getting the content_type id
                    cursor.execute(
                        "SELECT id from django_content_type "
                        "WHERE app_label='core' AND model=%s",
                        [target.lower()]
                    )
                    content_type_id = cursor.fetchall()
                    assert len(content_type_id) == 1
                    content_type_id = content_type_id[0][0]

                    # Create the wanted permission
                    print(f"Permission {codename} was not found. Creating it")
                    cursor.execute(
                        "INSERT INTO auth_permission (name, content_type_id, codename) "
                        "VALUES (%s, %s, %s)",
                        [description, content_type_id, codename]
                    )


                else:
                    print(f"Permission {codename} was found. Skipping")
                    continue

def update_django_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return

        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT auth_permission.id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model FROM auth_permission "
            "INNER JOIN django_content_type on auth_permission.content_type_id = django_content_type.id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' AND django_content_type.app_label = 'core'"
        )
        results = cursor.fetchall()

        if results:
            for id, codename, content_type_id, model_name in results:
                new_codename = f"{codename if codename != 'edit' else 'change'}_{model_name}"

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (new_codename, content_type_id)
                )
                new_permission_id = cursor.fetchall()
                # New permission not found. This is problematic if the target model is contract, dataset or project...
                # ... and if the permission is a default one.
                if not new_permission_id:
                    if codename in ['admin', 'protected'] \
                            and model_name not in ['contract', 'dataset', 'project']:
                        continue
                    else:
                        raise ValueError(f"No permission was found for codename={new_codename} and content_type_id={content_type_id}")
                else:
                    assert len(new_permission_id) == 1
                    new_permission_id, = new_permission_id[0]
                    print(f"Replacing old permission {codename} (id={id}, target={model_name}) by {new_codename} (id={new_permission_id})")
                    cursor.execute(
                        "UPDATE core_user_user_permissions "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s ",
                        (new_permission_id, id)
                    )

def update_guardian_userobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return
        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model FROM guardian_userobjectpermission "
            "INNER JOIN django_content_type on guardian_userobjectpermission.content_type_id = django_content_type.id "
            "INNER JOIN auth_permission on auth_permission.id = guardian_userobjectpermission.permission_id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' AND django_content_type.app_label = 'core'"
            "GROUP BY permission_id, auth_permission.codename, auth_permission.content_type_id, django_content_type.model"
        )
        results = cursor.fetchall()
        if results:
            for id, codename, content_type_id, model_name in results:
                new_codename = f"{codename if codename != 'edit' else 'change'}_{model_name}"

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (new_codename, content_type_id)
                )
                new_permission_id = cursor.fetchall()
                if not new_permission_id:
                    raise ValueError(f"No permission was found for codename={new_codename} and content_type_id={content_type_id}")
                else:
                    assert len(new_permission_id) == 1
                    new_permission_id, = new_permission_id[0]
                    print(f"Replacing old permission {codename} (id={id}, target={model_name}) by {new_codename} (id={new_permission_id})")
                    cursor.execute(
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (new_permission_id, id, content_type_id)
                    )


def update_core_datasetuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return
        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_datasetuserobjectpermission "
            "INNER JOIN auth_permission on auth_permission.id = core_datasetuserobjectpermission.permission_id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' "
            "GROUP BY permission_id, auth_permission.codename"
        )

        results = cursor.fetchall()
        if results:
            model_name = 'dataset'
            cursor.execute(
                "SELECT id from django_content_type "
                "WHERE app_label='core' and model = 'dataset'"
            )
            content_type_id = cursor.fetchone()[0]
            for id, codename in results:
                new_codename = f"{codename if codename != 'edit' else 'change'}_{model_name}"

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (new_codename, content_type_id)
                )
                new_permission_id = cursor.fetchall()
                if not new_permission_id:
                    raise ValueError(f"No permission was found for codename={new_codename} and content_type_id={content_type_id}")
                else:
                    assert len(new_permission_id) == 1
                    new_permission_id, = new_permission_id[0]
                    print(f"Replacing old permission {codename} (id={id}, target={model_name}) by {new_codename} (id={new_permission_id})")
                    cursor.execute(
                        "UPDATE core_datasetuserobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s",
                        (new_permission_id, id)
                    )


def update_core_projectuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return
        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_projectuserobjectpermission "
            "INNER JOIN auth_permission on auth_permission.id = core_projectuserobjectpermission.permission_id "
            "WHERE auth_permission.codename NOT LIKE '%\_%' "
            "GROUP BY permission_id, auth_permission.codename"
        )

        results = cursor.fetchall()
        if results:
            model_name = 'project'
            cursor.execute(
                "SELECT id from django_content_type "
                "WHERE app_label='core' and model = 'project'"
            )
            content_type_id = cursor.fetchone()[0]
            for id, codename in results:
                new_codename = f"{codename if codename != 'edit' else 'change'}_{model_name}"

                # Finding the new permission to use
                cursor.execute(
                    "SELECT id from auth_permission "
                    "WHERE auth_permission.codename=%s and auth_permission.content_type_id=%s",
                    (new_codename, content_type_id)
                )
                new_permission_id = cursor.fetchall()
                if not new_permission_id:
                    raise ValueError(f"No permission was found for codename={new_codename} and content_type_id={content_type_id}")
                else:
                    assert len(new_permission_id) == 1
                    new_permission_id, = new_permission_id[0]
                    print(f"Replacing old permission {codename} (id={id}, target={model_name}) by {new_codename} (id={new_permission_id})")
                    cursor.execute(
                        "UPDATE core_projectuserobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s",
                        (new_permission_id, id)
                    )

def update_group_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
        if is_test_environment(cursor):
            return
        for group, permissions_dict in GROUP_PERMISSIONS.items():
            # Find the group id
            cursor.execute(
                "SELECT id from auth_group "
                "WHERE auth_group.name=%s",
                [group.value]
            )

            group_id = cursor.fetchall()
            if not group_id:
                raise DataError(f"Group {group.value} was not found in database")

            try:
                assert len(group_id) == 1
            except AssertionError:
                raise DataError(f"More than one group named {group.value} was found in database")

            group_id = group_id[0][0]

            for model_label, permissions_list in permissions_dict.items():
                app_label, model_name = model_label.lower().split('.')
                for perm in permissions_list:
                    _, perm = perm.split('.')
                    # Get permission id
                    cursor.execute(
                        "SELECT auth_permission.id from auth_permission "
                        "INNER JOIN django_content_type ON django_content_type.id=auth_permission.content_type_id "
                        "WHERE auth_permission.codename=%s AND django_content_type.app_label=%s AND django_content_type.model=%s",
                        [perm, app_label, model_name]
                    )
                    perm_id = cursor.fetchall()
                    if not perm_id:
                        raise DataError(f"Permission {perm} (content_type={model_name}) was not found in database")

                    try:
                        assert len(perm_id) == 1
                    except AssertionError:
                        raise DataError(f"More than one permission {perm} (content_type={model_name}) was found in database")

                    perm_id = perm_id[0][0]
                    cursor.execute(
                        "INSERT INTO auth_group_permissions (group_id, permission_id)"
                        "VALUES (%s, %s)",
                        [group_id, perm_id]
                    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_update_model_permissions'),
    ]
    print("\n")

    operations = [
        migrations.RunPython(create_new_permissions, rollback_new_permissions),
        migrations.RunPython(update_django_permissions, rollback_django_permissions),
        migrations.RunPython(update_guardian_userobjectpermissions, rollback_guardian_userobjectpermissions),
        migrations.RunPython(update_core_datasetuserobjectpermissions, rollback_core_datasetuserobjectpermissions),
        migrations.RunPython(update_core_projectuserobjectpermissions, rollback_core_projectuserobjectpermissions),
        migrations.RunPython(update_group_permissions, rollback_group_permissions),
    ]
