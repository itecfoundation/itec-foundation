# Generated by Django 3.1.1 on 2022-05-06 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0006_questionnaire_pub_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='shortanswer',
            name='question_type',
            field=models.TextField(default='Short Answer'),
        ),
    ]
