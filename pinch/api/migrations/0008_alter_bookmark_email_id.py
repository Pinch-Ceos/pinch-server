# Generated by Django 3.2.5 on 2021-07-16 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_user_label_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='email_id',
            field=models.CharField(max_length=100),
        ),
    ]