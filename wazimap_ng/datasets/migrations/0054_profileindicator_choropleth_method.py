# Generated by Django 2.2.10 on 2020-03-30 20:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0005_auto_20200330_2005'),
        ('datasets', '0053_dataset_geography_hierarchy'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileindicator',
            name='choropleth_method',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='profile.ChoroplethMethod'),
        ),
    ]
