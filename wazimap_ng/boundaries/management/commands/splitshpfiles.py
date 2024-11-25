import os
from typing import Any, Dict

import shapefile
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    This command reads shapefiles in a specific path and splits them
    into smaller files based on the level so that they can correctly be
    loaded with the appropriate level using the `loadshp` command into
    the geography hierarchy.

    e.g:
    If the source looks like:

    Country/
    └── country.shp

    and the shapefile contains different levels: City, Town and District. The output will be:
    Country/
    └── <output-dir>/
        ├── City.shp
        ├── Town.shp
        └── District.shp
    """

    help = "Splits shapefiles in a directory into files based on the level."

    def add_arguments(self, parser):
        parser.add_argument(
            "directory", type=str, help="Directory containing shapefiles to be rebuilt."
        )
        parser.add_argument(
            "level_key",
            type=str,
            help="List of keys in the shapefile record that could contain the level.",
        )
        parser.add_argument(
            "output_dir",
            type=str,
            nargs="?",
            default="output",
            help="Directory to split the shapefiles into. Any directories with this name will also be skipped.",
        )

    def handle(self, *args, **options):
        # open the directory and read all shapefiles in the directory
        directory = options["directory"]
        level_keys = [f.strip() for f in options["level_key"].split(",")]
        output_dir = options["output_dir"]

        # check if directory exists
        if not os.path.isdir(directory):
            self.stderr.write(
                self.style.ERROR(f"Directory '{directory}' does not exist.")
            )
            return

        # read all files that end with .shp and store the paths without the extensions
        # Exclude the output directory from the list
        shapefiles_paths = []
        for root, dirs, files in os.walk(directory):
            if output_dir in dirs:
                dirs.remove(output_dir)
            for file in files:
                if file.endswith(".shp"):
                    shapefiles_paths.append(
                        os.path.splitext(os.path.join(root, file))[0]
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(shapefiles_paths)} shapefiles in '{directory}'."
            )
        )

        # open each shapefile and rebuild them into separate files
        # based on the level of each entry in the shapefile
        for shapefile_path in shapefiles_paths:
            self.stdout.write(f"Rebuilding shapefile '{shapefile_path}'...")

            level_shapefile_map: Dict[str, Any] = {}

            sf = shapefile.Reader(shapefile_path)
            for shape_record in sf.shapeRecords():
                props = shape_record.__geo_interface__["properties"]
                key = None
                level = None
                for key in level_keys:
                    if key in props:
                        key = key
                        level = props[key]
                        break

                if not key:
                    warning = (
                        "Shapefile fields do not contain any of the level keys. Skipping record.\n"
                        f"Keys are: {', '.join(level_keys)}\n"
                        f"Fields are: {', '.join(props.keys())}"
                    )
                    self.stderr.write(self.style.WARNING(warning))
                    continue

                if not level:
                    warning = (
                        f"Level field '{key}' is empty. Skipping record.\n"
                        f"Record is: {props}"
                    )
                    self.stderr.write(self.style.WARNING(warning))
                    continue

                if level not in level_shapefile_map:
                    # Create a new shapefile for the level and copy over all the fields
                    new_path = os.path.join(
                        os.path.dirname(shapefile_path), output_dir, level
                    )
                    new_sf = shapefile.Writer(new_path)
                    for field in sf.fields:
                        new_sf.field(*field)
                    level_shapefile_map[level] = new_sf

                # Add this record and shape to this level's shapefile
                new_sf = level_shapefile_map[level]
                new_sf.record(*shape_record.record)
                new_sf.shape(shape_record.shape)

            # Close all the shapefile writers and write the files
            for level, new_sf in level_shapefile_map.items():
                new_sf.close()
                self.stdout.write(f"Created shapefile for level '{level}'.")
