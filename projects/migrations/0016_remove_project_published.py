# Generated by Django 2.2.8 on 2020-02-29 08:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_auto_20200218_0753_squashed_0016_community_bank_account_bank_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='published',
        ),
    ]