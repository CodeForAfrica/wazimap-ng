"""
Management Command: create_profile_indicators

This command allows you to create `ProfileIndicator` objects for a given profile.
It mirrors the logic of the `ProfileIndicatorAdmin` form but creates the objects in bulk.

It generates labels using geography names and creates subcategories for the indicators
based on the "Annual Temperature" and "Temperature Variation" categories.

"""

from django.core.management.base import BaseCommand
from wazimap_ng.datasets.models import Geography
from wazimap_ng.profile.models import Profile, Indicator, IndicatorCategory, IndicatorSubcategory, ProfileIndicator
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = 'Create ProfileIndicator objects for a profile'

    def add_arguments(self, parser):
        parser.add_argument('profile_name', type=str, help="Name of the profile for which indicators will be created.")
        parser.add_argument('--description', type=str, help="Description for the profile indicator.", default="Default Description")
        parser.add_argument('--choropleth_method', type=str, help="Choropleth method to apply.", default="None")

    @transaction.atomic
    def handle(self, *args, **options):
        profile_name = options['profile_name']
        description = options['description']
        choropleth_method = options['choropleth_method']

        try:
            profile = Profile.objects.get(name=profile_name)
        except Profile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Profile with name '{profile_name}' does not exist."))
            return

        annual_temp_category_name = "Annual Temperature"
        temp_variation_category_name = "Temperature Variation"

        annual_category, _ = IndicatorCategory.objects.get_or_create(name=annual_temp_category_name, profile=profile)
        variation_category, _ = IndicatorCategory.objects.get_or_create(name=temp_variation_category_name, profile=profile)

        indicators = Indicator.objects.filter(dataset__profile=profile)
        if not indicators.exists():
            self.stdout.write(self.style.WARNING(f"No indicators found for profile '{profile_name}'."))
            return

        profile_indicators_to_create = []

        for indicator in indicators:
            try:
                geography_code = indicator.name.split("|")[0].strip()  # AO.BG
                geography = Geography.objects.get(code=geography_code)
                geography_name = geography.name

                # Determine the label and subcategory based on the indicator name
                if "Annual" in indicator.name:
                    label = f"{geography_name} Annual Temperature"
                    subcategory, _ = IndicatorSubcategory.objects.get_or_create(
                        name="Annual Temperature",
                        category=annual_category,
                        defaults={"description": "Annual Temperature Subcategory"}
                    )
                elif "Variation" in indicator.name:
                    label = f"{geography_name} Decadal Temperature Variation"
                    subcategory, _ = IndicatorSubcategory.objects.get_or_create(
                        name="Decadal Temperature Variation",
                        category=variation_category,
                        defaults={"description": "Decadal Temperature Variation Subcategory"}
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"Skipping indicator {indicator.name}: Unrecognized type."))
                    continue

                # Create the ProfileIndicator object
                profile_indicator = ProfileIndicator(
                    profile=profile,
                    indicator=indicator,
                    subcategory=subcategory,
                    label=label,
                    description=description,
                    choropleth_method=choropleth_method
                )
                profile_indicators_to_create.append(profile_indicator)

            except Geography.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Skipping indicator {indicator.name}: Geography code '{geography_code}' does not exist."))
            except ObjectDoesNotExist:
                self.stdout.write(self.style.WARNING(f"Skipping indicator {indicator.name}: Subcategory does not exist."))

        if profile_indicators_to_create:
            ProfileIndicator.objects.bulk_create(profile_indicators_to_create)
            self.stdout.write(self.style.SUCCESS(f"Successfully created {len(profile_indicators_to_create)} profile indicators for profile '{profile_name}'."))
        else:
            self.stdout.write(self.style.WARNING(f"No profile indicators were created for profile '{profile_name}'."))

