# Generated by Django 2.2.21 on 2021-08-04 03:30

from django.db import migrations

def update_geographies_and_related_data(apps, schema_editor):
    Version = apps.get_model("datasets", "Version")
    GeographyHierarchy = apps.get_model("datasets", "GeographyHierarchy")
    Geography = apps.get_model("datasets", "Geography")
    Dataset = apps.get_model("datasets", "Dataset")
    GeographyBoundary = apps.get_model("boundaries", "GeographyBoundary")

    cached_version_by_name = {v.name: v for v in Version.objects.all()}

    for boundary in GeographyBoundary.objects.all():
        boundary.version = cached_version_by_name[boundary.geography.version]
        boundary.save()

    for dataset in Dataset.objects.all():
        hierarchy_version_name = dataset.geography_hierarchy.root_geography.version
        dataset.version = cached_version_by_name[hierarchy_version_name]
        dataset.save()

    for hierarchy in GeographyHierarchy.objects.all():
        hierarchy.configuration["default_version"] = hierarchy.root_geography.version
        hierarchy.save()


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0116_auto_20210803_2049'),
    ]

    operations = [
        migrations.RunPython(update_geographies_and_related_data),
    ]
