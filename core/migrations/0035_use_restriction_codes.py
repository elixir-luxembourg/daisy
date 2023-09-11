from django.db import migrations


def apply_code_map(objects, field, reverse=False):
    code_map = [
        ("GRU(CC)", "GRU"),
        ("HMB(CC)", "HMB"),
        ("DS-[XX](CC)", "DS"),
        ("RS-[XX]", "RS"),
        ("COL-[XX]", "COL"),
        ("GS-[XX]", "GS"),
        ("MOR-[XX]", "MOR"),
        ("TS-[XX]", "TS"),
    ]
    if reverse:
        code_map = list(map(tuple, map(reversed, code_map)))

    for obj in objects:
        for code_mapping in code_map:
            if getattr(obj, field) == code_mapping[0]:
                setattr(obj, field, code_mapping[1])
                obj.save()


class Migration(migrations.Migration):
    def restriction_use_code_to_new(apps, schema_editor):
        use_restriction_objects = apps.get_model("core", "UseRestriction").objects.all()
        apply_code_map(objects=use_restriction_objects, field="restriction_class")

    def restriction_use_code_to_old(apps, schema_editor):
        use_restriction_objects = apps.get_model("core", "UseRestriction").objects.all()
        apply_code_map(use_restriction_objects, field="restriction_class", reverse=True)

    def restriction_class_code_to_new(apps, schema_editor):
        use_class_objects = apps.get_model("core", "RestrictionClass").objects.all()
        apply_code_map(objects=use_class_objects, field="code")

    def restriction_class_code_to_old(apps, schema_editor):
        use_class_objects = apps.get_model("core", "RestrictionClass").objects.all()
        apply_code_map(use_class_objects, field="code", reverse=True)

    dependencies = [
        ("core", "0034_auto_20230515_1353"),
    ]

    operations = [
        migrations.RunPython(restriction_use_code_to_new, restriction_use_code_to_old),
        migrations.RunPython(
            restriction_class_code_to_new, restriction_class_code_to_old
        ),
    ]
