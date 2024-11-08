"""
This model creates a new command that generates children of geographies.
It uses the GeographyHierarchy model to get the root geography and the Version model to get the version.
It then prints the children of the root geography and their children accordingly
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db.transaction import atomic
from pathlib import Path

from tests.profile.serializers.test_indicator_data_for_children import profile
from wazimap_ng.datasets.models import Dataset, DatasetFile, Version
from wazimap_ng.profile.models import Profile
from wazimap_ng.datasets.models import Geography, GeographyHierarchy, Version
from wazimap_ng.constants import PERMISSION_TYPES


class Command(BaseCommand):
    help = "Generates children of geographies"

    def handle(self, *args, **options):
        geography_hierarchy = GeographyHierarchy.objects.first()
        version = Version.objects.get(name="Climate")
        root_geography = geography_hierarchy.root_geography
        final_hierarchy = {}
        self.build_hierarchy(root_geography, version, final_hierarchy)

        # CLean the hashmap to remove empty sets and convert the sets to lists
        cleaned_hierarchy = {
            key: list(value) for key, value in final_hierarchy.items() if value
        }
        print(cleaned_hierarchy)

    def build_hierarchy(self, geography, version, final_hierarchy):
        if geography.level not in final_hierarchy:
            final_hierarchy[geography.level] = set()

        children = geography.get_child_geographies(version)
        for child in children:
            final_hierarchy[geography.level].add(child.level)
            self.build_hierarchy(child, version, final_hierarchy)

