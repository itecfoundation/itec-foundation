# Generated by Django 2.2.8 on 2020-07-29 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0045_auto_20200725_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='platform_policy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='community',
            name='privacy_policy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='platform_policy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='privacy_policy',
            field=models.BooleanField(default=False),
        ),
    ]
