# Generated by Django 3.2.5 on 2021-07-21 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_remove_user_last_email_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='read_num',
            field=models.IntegerField(default=0),
        ),
    ]