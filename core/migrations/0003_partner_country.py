# Generated by Django 2.1.9 on 2019-07-15 13:22

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_auto_20190715_1042"),
    ]

    operations = [
        migrations.AddField(
            model_name="partner",
            name="country",
            field=django_countries.fields.CountryField(
                blank=True, max_length=2, null=True
            ),
        ),
    ]
