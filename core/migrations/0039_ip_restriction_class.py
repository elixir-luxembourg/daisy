from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_auto_20241018_1733"),
    ]

    def add_ip_restriction_class(apps, schema_editor):
        restriction_class_model = apps.get_model("core", "RestrictionClass")
        restriction_class_model.objects.get_or_create(
            code="IP",
            name="IP claim terms",
            description="Intellectual property rights claims.",
        )

        restriction_class_model.objects.get_or_create(
            code="Other",
            name="Other use restrictions",
            description="Other use restrictions.",
        )

    operations = [migrations.RunPython(add_ip_restriction_class)]
