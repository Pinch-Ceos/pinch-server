# Generated by Django 3.2.5 on 2021-07-10 00:54

from django.db import migrations
import oauth2client.contrib.django_util.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20210710_0034'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='credential',
            field=oauth2client.contrib.django_util.models.CredentialsField(null=True),
        ),
    ]