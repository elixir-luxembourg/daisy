# Generated by Django 2.2.28 on 2022-04-29 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20211004_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userestriction',
            name='notes',
            field=models.TextField(blank=True, help_text='Provide a free text description of the restriction.', null=True, verbose_name='Use Restriction note'),
        ),
    ]
