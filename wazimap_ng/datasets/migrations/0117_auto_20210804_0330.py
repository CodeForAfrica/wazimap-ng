# Generated by Django 2.2.21 on 2021-08-04 03:30

from django.db import migrations
# Must import to use treebeard API
from wazimap_ng.datasets.models import Geography

def update_geographies_and_related_data(apps, schema_editor):
    Version = apps.get_model("datasets", "Version")
    GeographyHierarchy = apps.get_model("datasets", "GeographyHierarchy")
    DatasetData = apps.get_model("datasets", "DatasetData")
    Dataset = apps.get_model("datasets", "Dataset")
    GeographyBoundary = apps.get_model("boundaries", "GeographyBoundary")
    IndicatorData = apps.get_model("datasets", "IndicatorData")

    kept_geos_by_code = dict()
    kept_geos_parent_code_by_id = dict()
    geo_ids_to_delete = set()

    # Order by depth so that we decide which parent to keep before
    # deciding which children to keep and can move kept children to kept parents.
    geo_codes = Geography.objects.all().values_list(
        "code", flat=True
    ).order_by("code").distinct()

    for code in geo_codes:
        geography_objs = Geography.objects.filter(code=code)
        first_geo_obj = geography_objs.first()
        kept_geos_by_code[code] = first_geo_obj;
        kept_geos_parent_code_by_id[first_geo_obj.id] = first_geo_obj.get_parent().code
        print(f"Keeping {code} with id {first_geo_obj.id}")

        # get versions and assign it to first geo obj
        version_list = geography_objs.values_list("version", flat=True).order_by("version").distinct()
        versions_qs = Version.objects.filter(name__in=version_list)
        first_geo_obj.versions.add(*versions_qs)

        # Update version for first Geography version
        first_geo_version = versions_qs.get(name=first_geo_obj.version)
        GeographyBoundary.objects.filter(geography=first_geo_obj).update(
            version=first_geo_version
        )
        dataset_list = DatasetData.objects.filter(
            geography=first_geo_obj
        ).values_list("dataset_id", flat=True)
        Dataset.objects.filter(id__in=dataset_list).update(version=first_geo_version)
        GeographyHierarchy.objects.filter(root_geography=first_geo_obj).update(
            configuration={
                "versions": [first_geo_obj.version],
                "default_version": first_geo_obj.version
            }
        )

        # Change related data to geo objs that will be deleted
        geography_objs_to_delete = geography_objs.exclude(id=first_geo_obj.id)
        for geo_obj in geography_objs_to_delete:
            geo_ids_to_delete.add(geo_obj.id)
            version = versions_qs.get(name=geo_obj.version)
            # Update boundaries
            GeographyBoundary.objects.filter(geography=geo_obj).update(
                geography=first_geo_obj, version=version
            )

            # Update DatasetData & Dataset
            dataset_data = DatasetData.objects.filter(geography=geo_obj)
            Dataset.objects.filter(
                id__in=dataset_data.values_list("dataset_id", flat=True)
            ).update(version=version)
            dataset_data.update(geography=first_geo_obj)

            # Update IndicatorData
            IndicatorData.objects.filter(geography=geo_obj).update(geography=first_geo_obj)

            # GeographyHierarchy
            GeographyHierarchy.objects.filter(root_geography=geo_obj).update(
                configuration={"versions": [geo_obj.version]}, root_geography=first_geo_obj
            )

    for id in geo_ids_to_delete:
        Geography.objects.filter(id=id).delete()

    for geo in Geography.objects.all():
        # update parent to the one we're keeping which has the same code
        geo.move(kept_geos_by_code[kept_geos_parent_code_by_id[geo.id]], 'last-child')



class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0116_auto_20210803_2049'),
    ]

    operations = [
        migrations.RunPython(update_geographies_and_related_data),
    ]
