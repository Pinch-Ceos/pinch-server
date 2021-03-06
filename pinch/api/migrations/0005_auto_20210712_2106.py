# Generated by Django 3.2.5 on 2021-07-12 21:06

from django.db import migrations, models
import django.db.models.deletion
import oauth2client.contrib.django_util.models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20210711_1655'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='credential',
        ),
        migrations.CreateModel(
            name='Credentials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('credential', oauth2client.contrib.django_util.models.CredentialsField(null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='api.user')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
