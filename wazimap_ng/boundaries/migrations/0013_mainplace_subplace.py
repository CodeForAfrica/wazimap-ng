# Generated by Django 2.2.8 on 2020-01-21 12:11

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0012_auto_20200121_1158'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mainplace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('name', models.CharField(max_length=254)),
                ('municipality_code', models.CharField(max_length=7)),
                ('municipality_name', models.CharField(max_length=254)),
                ('area', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='Subplace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=9)),
                ('name', models.CharField(max_length=254)),
                ('mainplace_code', models.CharField(max_length=6)),
                ('area', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
        ),
    ]
