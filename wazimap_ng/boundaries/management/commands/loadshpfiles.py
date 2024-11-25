from glob import glob

import shapefile
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    This command reads shapefiles in a specific path and calls the loadshp command for each shapefile
    with the correct arguments. based on the passed in keys and values.

    If the source directory contains a single shapefile then it is equivalent to calling the loadshp command
    directly
    """

    help = "Loads matching shapefiles into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "files",
            type=str,
            help="Glob pattern matching shapefiles to be loaded e.g. ./regions/*/rebuilt/*.shp",
        )
        parser.add_argument(
            "code_keys",
            type=str,
            help="List of possible fields in the shapefile to extract the code from. They are checked in order",
        )
        parser.add_argument(
            "name_keys",
            type=str,
            help="List of possible fields in the shapefile to extract the name from. They are checked in order",
        )
        parser.add_argument(
            "parent_code_keys",
            type=str,
            help="List of possible fields in the shapefile to extract the parent code from. They are checked in order",
        )
        parser.add_argument(
            "area_keys",
            type=str,
            help="List of possible fields in the shapefile to extract the area from. They are checked in order",
        )
        parser.add_argument(
            "level_keys",
            type=str,
            help="List of possible fields in the shapefile to extract the level from. They are checked in order",
        )
        parser.add_argument("hierarchy", type=str, help="Geography hierarchy name.")
        parser.add_argument("version", type=str, help="Version of the geography.")

    def handle(self, *args, **options):
        files_pattern = options["files"]
        code_keys = [f.strip() for f in options["code_keys"].split(",")]
        name_keys = [f.strip() for f in options["name_keys"].split(",")]
        parent_code_keys = [f.strip() for f in options["parent_code_keys"].split(",")]
        area_keys = [f.strip() for f in options["area_keys"].split(",")]
        level_keys = [f.strip() for f in options["level_keys"].split(",")]
        hierarchy = options["hierarchy"]
        version = options["version"]

        # Check if any files were matched
        files = glob(files_pattern, recursive=True)
        if not files:
            self.stderr.write(
                self.style.WARNING(
                    f"No files found matching the pattern {files_pattern}"
                )
            )
            return

        print(f"Found {len(files)} files matching the pattern {files_pattern}")
        for file in files:
            print(f"Processing {file}")
            sf = shapefile.Reader(file)
            field_names = [f[0] for f in sf.fields[1:]]

            code_field = None
            name_field = None
            parent_code_field = None
            area_field = None
            level = None

            # Extract the value in the code field
            for code_key in code_keys:
                if code_key in field_names:
                    code_field = code_key
                    break

            if not code_field:
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not find a code field in the shapefile {file}"
                    )
                )
                continue

            # Extract the name field
            for name_key in name_keys:
                if name_key in field_names:
                    name_field = name_key
                    break

            if not name_field:
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not find a name field in the shapefile {file}"
                    )
                )
                continue

            # Extract the parent code field
            for parent_code_key in parent_code_keys:
                if parent_code_key in field_names:
                    parent_code_field = parent_code_key
                    break

            if not parent_code_field:
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not find a parent code field in the shapefile {file}"
                    )
                )
                continue

            # Extract the area field
            for area_key in area_keys:
                if area_key in field_names:
                    area_field = area_key
                    break

            if not area_field:
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not find an area field in the shapefile {file}"
                    )
                )
                continue

            # Extract the level field value from the shapefile
            for level_key in level_keys:
                if level_key in field_names:
                    level = sf.records()[0][level_key]
                    break

            if not level:
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not find a level field in the shapefile {file}"
                    )
                )
                continue

            # call the loadshp command with the correct arguments
            call_command(
                "loadshp",
                file,
                f"{code_field}=code,{name_field}=name,{parent_code_field}=parent_code,{area_field}=area",
                hierarchy,
                level,
                version,
            )
