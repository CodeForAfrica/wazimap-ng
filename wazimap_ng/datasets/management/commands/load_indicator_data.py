"""
Management Command: update_indicators

This command updates `Indicator` objects based on datasets found in the system (Annual Temperature and Temperature Variation).

- It filters datasets that have 'Annual' or 'Variation' in their names.
- For datasets with 'Annual', it takes the first group from the `groups` field and creates a new `Indicator` (year).
- For datasets with 'Variation', it checks if 'period' exists in `groups`, and if so, creates the `Indicator` with 'period' as the group. Otherwise, it defaults to the first group.
- All new `Indicator` objects are created in bulk for performance optimization.

This is a temporary command used to populate the `Indicator` table based on existing datasets.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.core.files import File
from django.db.transaction import atomic
from pathlib import Path

from wazimap_ng.datasets.models import Dataset, Indicator


class Command(BaseCommand):
    help = "Create Indicator objects based on the datasets"

    def handle(self, *args, **kwargs):
        self.add_indicator_data()

    def add_indicator_data(self):
        datasets = Dataset.objects.all()
        indicators_to_create = []

        for dataset in datasets:
            groups = None

            if "Annual" in dataset.name:
                groups = [dataset.groups[0]] if dataset.groups else []
            elif 'Variation' in dataset.name:
                if 'period' in dataset.groups:
                    groups = ['period']
                else:
                    groups = [dataset.groups[0]] if dataset.groups else []

            if groups:
                indicators_to_create.append(Indicator(dataset=dataset, name=dataset.name, groups=groups))

        Indicator.objects.bulk_create(indicators_to_create)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(indicators_to_create)} indicators."))
