# Generated by Django 3.1.1 on 2022-03-27 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0006_redirect_increase_max_length'),
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
        ('wagtailforms', '0004_add_verbose_name_plural'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homepage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='learnmore',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='list',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='termsandconditions',
            name='page_ptr',
        ),
        migrations.DeleteModel(
            name='AboutUs',
        ),
        migrations.DeleteModel(
            name='HomePage',
        ),
        migrations.DeleteModel(
            name='LearnMore',
        ),
        migrations.DeleteModel(
            name='List',
        ),
        migrations.DeleteModel(
            name='TermsAndConditions',
        ),
    ]
