from django.db import migrations, connection, DataError

# BEFORE UPGRADE:
# Django default permissions can be safely upgraded?
# - PROTECTED is given on documents -> Needs to be skipped (protected only attributed to projects and contracts atm)
#

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
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (old_permission_id, id, content_type_id)
                    )
        else:
            print("No new permission was found on datasets. Nothing to roll back.")


def rollback_core_projectuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be put back in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_projectuserobjectpermissions "
            "INNER JOIN auth_permission on auth_permission.id = core_projectuserobjectpermissions.permission_id "
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
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (old_permission_id, id, content_type_id)
                    )
        else:
            print("No new permission was found on projects. Nothing to roll back.")


def update_django_permissions(apps, schema_editor):
    with connection.cursor() as cursor:
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
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (new_permission_id, id, content_type_id)
                    )


def update_core_projectuserobjectpermissions(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting the list of old permissions that need to be replaced in permission attributions
        cursor.execute(
            "SELECT permission_id, auth_permission.codename FROM core_projectuserobjectpermissions "
            "INNER JOIN auth_permission on auth_permission.id = core_projectuserobjectpermissions.permission_id "
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
                        "UPDATE guardian_userobjectpermission "
                        "SET permission_id=%s "
                        "WHERE permission_id=%s and content_type_id=%s",
                        (id, content_type_id)
                    )


def rollback_local_custodians_protected_permission(apps, schema_editor):
    with connection.cursor() as cursor:
        # Getting permission ids
        cursor.execute(
            "SELECT id, codename from auth_permission "
            "WHERE codename = 'protected_contract' "
            "OR codename = 'protected_dataset' "
            "OR codename = 'protected_project'"
        )
        results = cursor.fetchall()
        id_dict = {perm_codename: perm_id for perm_codename, perm_id in results}

        # Deleting protected permission on datasets
        cursor.execute(
            "DELETE FROM core_datasetuserobjectpermission "
            "WHERE permission_id = %s",
            [id_dict['protected_dataset']]
        )

        # Deleting protected permission on projects
        cursor.execute(
            "DELETE FROM core_projectuserobjectpermission "
            "WHERE permission_id = %s",
            [id_dict['protected_project']]
        )

        # Deleting protected permission on contracts
        cursor.execute(
            "DELETE FROM guardian_userobjectpermission "
            "WHERE permission_id = %s",
            [id_dict['protected_contract']]
        )


def add_protected_permission_to_local_custodians(apps, schema_editor):
    with connection.cursor() as cursor:
        # Update contract custodians
        cursor.execute(
            "SELECT django_content_type.id, auth_permission.id from django_content_type "
            "INNER JOIN auth_permission ON django_content_type.id = auth_permission.content_type_id "
            "WHERE app_label='core' AND model='contract' AND codename='protected_contract'"
        )
        contract_content_type_id, permission_id = cursor.fetchone()
        print(f"Contract ct id is {contract_content_type_id}")
        print(f"New permission id is {permission_id}")

        cursor.execute(
            "SELECT contract_id, user_id from core_contract_local_custodians"
        )

        results = cursor.fetchall()
        rows_to_insert = ""
        cols = "(object_pk, content_type_id, permission_id, user_id)"
        for contract_id, user_id in results:
            rows_to_insert += f"({contract_id}, {contract_content_type_id}, {permission_id}, {user_id}), "

        rows_to_insert = rows_to_insert.rstrip(', ')
        # Inserting new data
        cursor.execute(
            "INSERT INTO guardian_userobjectpermission %s"
            "VALUES %s",
            [cols, rows_to_insert]
        )


        # Update project custodians
        cursor.execute(
            "SELECT id from auth_permission "
            "WHERE codename='protected_project'"
        )
        permission_id = cursor.fetchone()[0]
        print(f"New permission id is {permission_id}")

        cursor.execute(
            "SELECT project_id, user_id from core_project_local_custodians"
        )

        results = cursor.fetchall()
        rows_to_insert = ""
        cols = "(content_object_id, permission_id, user_id)"
        for project_id, user_id in results:
            rows_to_insert += f"({project_id}, {permission_id}, {user_id}), "

        rows_to_insert = rows_to_insert.rstrip(', ')
        # Inserting new data
        cursor.execute(
            "INSERT INTO core_projectuserobjectpermission %s"
            "VALUES %s",
            [cols, rows_to_insert]
        )

        cursor.execute(
            "SELECT id from auth_permission "
            "WHERE codename='protected_dataset'"
        )
        permission_id = cursor.fetchone()[0]
        print(f"New permission id is {permission_id}")

        cursor.execute(
            "SELECT dataset_id, user_id from core_dataset_local_custodians"
        )

        results = cursor.fetchall()
        rows_to_insert = ""
        cols = "(content_object_id, permission_id, user_id)"
        for dataset_id, user_id in results:
            rows_to_insert += f"({dataset_id}, {permission_id}, {user_id}), "

        rows_to_insert = rows_to_insert.rstrip(', ')
        # Inserting new data
        cursor.execute(
            "INSERT INTO core_projectuserobjectpermission %s"
            "VALUES %s",
            [cols, rows_to_insert]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_update_model_permissions'),
    ]
    print("\n")

    operations = [
        migrations.RunPython(update_django_permissions, rollback_django_permissions),
        migrations.RunPython(update_guardian_userobjectpermissions, rollback_guardian_userobjectpermissions),
        migrations.RunPython(update_core_datasetuserobjectpermissions, rollback_core_datasetuserobjectpermissions),
        migrations.RunPython(update_core_projectuserobjectpermissions, rollback_core_projectuserobjectpermissions),
        migrations.RunPython(add_protected_permission_to_local_custodians, rollback_local_custodians_protected_permission)
    ]
