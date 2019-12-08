# Generated by Django 2.1.9 on 2019-08-02 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_storage_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='expiry_date',
            field=models.DateField(blank=True, help_text='If the document has a validity period, please specify the expiry date here.', null=True, verbose_name='Expiry date'),
        ),
    ]