# Generated by Django 2.2.20 on 2021-05-18 12:58

import core.models.utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_auto_20210514_2222"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datalogtype",
            name="name",
            field=core.models.utils.TextFieldWithInputWidget(
                max_length=128, verbose_name="Name of the type of the event"
            ),
        ),
        migrations.AlterField(
            model_name="share",
            name="partner",
            field=models.ForeignKey(
                blank=True,
                help_text="The Partner involved in the data event.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shares",
                to="core.Partner",
                verbose_name="Involved partner",
            ),
        ),
    ]
