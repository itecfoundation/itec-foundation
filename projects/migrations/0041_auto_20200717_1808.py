# Generated by Django 2.2.8 on 2020-07-17 15:08

from django.db import migrations, models
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0040_auto_20200717_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donatordata',
            name='postAddress',
            field=models.CharField(max_length=200, verbose_name='postAdress'),
        ),
        migrations.AlterField(
            model_name='legalentitydonatordata',
            name='EIK',
            field=models.CharField(max_length=50, verbose_name='EIK'),
        ),
        migrations.AlterField(
            model_name='legalentitydonatordata',
            name='headquarters',
            field=django_countries.fields.CountryField(max_length=30, verbose_name='headquarters'),
        ),
        migrations.AlterField(
            model_name='legalentitydonatordata',
            name='postAddress',
            field=models.CharField(max_length=200, verbose_name='postAdress'),
        ),
    ]
