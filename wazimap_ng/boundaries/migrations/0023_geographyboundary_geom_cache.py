# Generated by Django 2.2.8 on 2020-02-14 10:14

from django.db import migrations
import wazimap_ng.boundaries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('boundaries', '0022_auto_20200214_0946'),
    ]

    operations = [
        migrations.AddField(
            model_name='geographyboundary',
            name='geom_cache',
            field=wazimap_ng.boundaries.fields.CachedMultiPolygonField(blank=True, null=True, srid=4326),
        ),
    ]
