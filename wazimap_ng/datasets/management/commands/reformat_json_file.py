"""
This command simply reads a JSON file and reads the featured_locations flag, correcting the level, for each of the entries
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db.transaction import atomic
from pathlib import Path
import json

from wazimap_ng.datasets.models import Dataset, DatasetFile, Version
from wazimap_ng.profile.models import Profile
from wazimap_ng.datasets.models import Geography, GeographyHierarchy, Version
from wazimap_ng.constants import PERMISSION_TYPES

class Command(BaseCommand):
    help = "Reads profile configuration and updates it with the correct level"

    def handle(self, *args, **options):
        # Build the map to store the final values
        code_level_map = {}
        geographies = Geography.objects.all()
        for geography in geographies:
            code_level_map[geography.code] = geography.level

        # Loop through the JSON object and update the level
        with open("datasets/climate_mapped_profile.json", 'r') as file:
            data = json.load(file)
            featured_locations = data.get("featured_locations", [])

            for location in featured_locations:
                if location["code"] not in code_level_map:
                    self.stdout.write(self.style.WARNING(f"Code [{location['code']}] not found in the database Geographies"))
                location["level"] = code_level_map.get(location["code"], location["level"])

            data["featured_locations"] = featured_locations

        # Write the updated JSON object back to the file
        with open("datasets/climate_mapped_profile.json", 'w') as file:
            json.dump(data, file, indent=2)