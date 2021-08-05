from django.db import models

from django.contrib.gis.db import models
from ..datasets.models import Geography, Version
from .fields import CachedMultiPolygonField
from ..points.models import Location
from django_q.tasks import async_task
from wazimap_ng.general.models import BaseModel

class GeographyBoundaryManager(models.Manager):
    # Deal with a situation where there are multiple geographies with the same code
    # TODO perhaps define a key to include level
    def get_unique_boundary(self, geography):
        #TODO might need to remove this now that code is not stored in the boundary
        obj = GeographyBoundary.objects.filter(geography__code=geography.code, geography__version=geography.version).first()
        return obj

class GeographyBoundary(BaseModel):
    geography = models.ForeignKey(Geography, on_delete=models.PROTECT, null=False)
    version = models.ForeignKey(Version, on_delete=models.PROTECT, null=True)
    area = models.FloatField()
    geom = models.MultiPolygonField(srid=4326, null=True)
    geom_cache = CachedMultiPolygonField(field_name="geom")
    objects = GeographyBoundaryManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["version", "geography"], name="unique_geography_version")
        ]
  
