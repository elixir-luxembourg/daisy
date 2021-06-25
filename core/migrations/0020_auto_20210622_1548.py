# Generated by Django 2.2.20 on 2021-06-22 13:48

import core.models.user
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20210616_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='api_key',
            field=models.CharField(default=core.models.user.create_api_key, help_text='A token used to authenticate the user for accessing API', max_length=64, verbose_name='API key'),
        ),
        migrations.AddField(
            model_name='user',
            name='oidc_id',
            field=models.CharField(blank=True, help_text="Internal user identifier coming from OIDC's IdP", max_length=64, null=True, verbose_name='OIDC user identifier'),
        ),
    ]