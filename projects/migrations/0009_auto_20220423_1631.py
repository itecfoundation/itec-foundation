# Generated by Django 3.1.1 on 2022-04-23 13:31

from django.db import migrations, models
import projects.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20220423_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='prezentation',
            field=models.FileField(blank=True, null=True, upload_to=projects.models.project_directory_path),
        ),
    ]
