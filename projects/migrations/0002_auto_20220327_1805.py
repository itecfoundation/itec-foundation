# Generated by Django 3.1.1 on 2022-03-27 18:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_authoradmin'),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='type',
        ),
        migrations.AddField(
            model_name='project',
            name='author_admin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.authoradmin'),
        ),
    ]
