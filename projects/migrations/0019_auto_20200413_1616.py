# Generated by Django 2.2.8 on 2020-04-13 13:16

from django.db import migrations, models
import django.db.models.deletion
import rules.contrib.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0018_auto_20200413_1557'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalEntityDonatorData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(editable=False)),
                ('updated_at', models.DateTimeField(editable=False)),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50)),
                ('EIK', models.CharField(max_length=50)),
                ('DDORegistration', models.BooleanField()),
                ('phoneNumber', models.CharField(max_length=30)),
                ('website', models.CharField(blank=True, max_length=30)),
            ],
            bases=(rules.contrib.models.RulesModelMixin, models.Model),
        ),
        migrations.AlterField(
            model_name='user',
            name='donatorData',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='projects.DonatorData'),
        ),
        migrations.AddField(
            model_name='user',
            name='legalEntityDonatorData',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='projects.LegalEntityDonatorData'),
        ),
    ]
