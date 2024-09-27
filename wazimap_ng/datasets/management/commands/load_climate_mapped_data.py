"""
Temporary command to bulk upload datasets from a specified directory.

This command loops through all CSV files in the given directory, extracts
the dataset name from the file name (formatted as 'KEY.VALUE|Dataset Name'),
and uploads the dataset to the database. It handles exceptions for
missing profiles and skips files that do not match the expected format.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.db.transaction import atomic
from pathlib import Path

from wazimap_ng.datasets.models import Dataset, DatasetFile, Version
from wazimap_ng.profile.models import Profile
from wazimap_ng.config.common import PERMISSION_TYPES

from django_q.tasks import async_task

class Command(BaseCommand):
    help = 'Uploads datasets from a specified directory.'

    def add_arguments(self, parser):
        parser.add_argument('profile_name', type=str, help="Name of profile as it exists in the database (case sensitive).")
        parser.add_argument('version', type=str, help="Version.")
        parser.add_argument('data_directory', type=str, help="Path to the directory containing files to be uploaded.")

    def load_file(self, profile, version, dataset_name, path):
        with atomic():
            # Defaults
            permission_type = 'public'

            dataset = Dataset.objects.create(profile=profile, version=version, name=dataset_name, permission_type=permission_type)
            df = DatasetFile.objects.create(name=dataset_name, dataset_id=dataset.pk, document=File(path.open("rb")))

            uuid = async_task(
                "wazimap_ng.datasets.tasks.process_uploaded_file",
                df, dataset,
                task_name=f"Uploading data from command: {dataset.name}",
                hook="wazimap_ng.datasets.hooks.process_task_info",
                key="No session",
                type="upload", assign=True, notify=False
            )

            return uuid

    def handle(self, *args, **options):
        profile_name = options["profile_name"]
        version = options["version"]
        data_directory = options["data_directory"]
        path = Path(data_directory)

        if not path.is_dir():
            raise CommandError(f'Could not find data directory at {data_directory}')

        try:
            profile = Profile.objects.get(name=profile_name)
            version = Version.objects.get(name=version)

            for file in path.glob('*.csv'):
                file_name = file.stem  # Get the file name without the extension
                parts = file_name.split('|')  # Split by '|'

                if len(parts) != 2:
                    self.stdout.write(self.style.WARNING(f'Skipping file {file_name}: does not match expected format.'))
                    continue

                dataset_name = f"{parts[0].strip()} | {parts[1].strip().replace('_', ' ')}"  # Format the dataset name
                uuid = self.load_file(profile, version, dataset_name, file)  # Load the file

        except Profile.DoesNotExist:
            profiles = ", ".join(p.name for p in Profile.objects.all())
            raise CommandError(f'Profile {profile_name} does not exist. The following profiles are available: {profiles}')

        self.stdout.write(f"All tasks submitted successfully.")
