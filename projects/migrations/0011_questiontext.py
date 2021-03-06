# Generated by Django 3.1.1 on 2022-05-22 18:07

from django.db import migrations, models
import rules.contrib.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_auto_20220522_1857'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(editable=False)),
                ('updated_at', models.DateTimeField(editable=False)),
                ('question_text', models.CharField(default='Please write the name of the person or organization that invited you to the project', max_length=200)),
                ('answer', models.TextField(blank=True, verbose_name='answer')),
            ],
            bases=(rules.contrib.models.RulesModelMixin, models.Model),
        ),
    ]
