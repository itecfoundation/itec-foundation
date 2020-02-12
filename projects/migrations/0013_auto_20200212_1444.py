# Generated by Django 2.2.8 on 2020-02-12 14:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_auto_20200211_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='project',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='projects.Project'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together={('project', 'question')},
        ),
        migrations.RemoveField(
            model_name='answer',
            name='time_support',
        ),
    ]