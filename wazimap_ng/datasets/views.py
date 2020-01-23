from django.http import Http404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework_csv import renderers as r
from rest_framework import generics
from .serializers import AncestorGeographySerializer, GeographySerializer
from . import serializers
from . import models
from . import mixins

class DatasetList(generics.ListAPIView):
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer

class DatasetIndicatorsList(generics.ListAPIView):
    queryset = models.Indicator.objects.all()
    serializer_class = serializers.IndicatorSerializer

    def get(self, request, dataset_id):
        if models.Dataset.objects.filter(id=dataset_id).count() == 0:
            raise Http404 

        queryset = self.get_queryset().filter(dataset=dataset_id)
        queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)

class IndicatorsList(generics.ListAPIView):
    queryset = models.Indicator.objects.all()
    serializer_class = serializers.IndicatorSerializer

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 10000


def truthy(s):
    return str(s).lower() == "true" or str(s) == 1

class IndicatorDataView(mixins.PaginatorMixin, generics.ListAPIView):
    queryset = models.DatasetData.objects.all()
    serializer_class = serializers.DataSerializer
    pagination_class = LargeResultsSetPagination

    def _filter_by_value(self, qs, indicator, values):
        def split_values(s):
            if ":" not in s:
                return {}

            return {
                pair.split(":", 1)[0]: pair.split(":", 1)[1]
                for pair in s.split(",")
            }

        values_dict = split_values(values)
        new_dict = {"data__" + k: v for k, v in values_dict.items() if k in indicator.groups}
        qs = qs.filter(**new_dict)

        return qs

    def _filter_by_geography(self, qs, geography_code, use_parent):
        if geography_code != None:
            if models.Geography.objects.filter(code=geography_code).count() == 0:
                raise Http404

            if use_parent:
                geography = models.Geography.objects.filter(code=geography_code).first()
                qs = qs.filter(geography__in=geography.get_children())
            else:
                qs = qs.filter(geography__code=geography_code)
        return qs

    def _paginate_response(self, qs, indicator):
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer_class()(page, group=indicator.groups, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer_class()(qs, group=indicator.groups, many=True)
        return Response(serializer.data)

    def get(self, request, indicator_id, geography_code=None):
        # TODO - this view is not yet finished - currently doesn't aggregate values - not sure if it should
        # May want to look at the add_indicator method of Profile
        use_parent = truthy(request.GET.get("parent", False))
        values = request.GET.get("values", "")

        indicator = models.Indicator.objects.get(id=indicator_id)
        queryset = self.get_queryset().filter(dataset=indicator.dataset)

        queryset = self._filter_by_geography(queryset, geography_code, use_parent)
        queryset = self._filter_by_value(queryset, indicator, values)
        return self._paginate_response(queryset, indicator)

class ProfileList(generics.ListAPIView):
    """
    Return a list of profiles
    """
    queryset = models.Profile.objects.all()
    serializer_class = serializers.ProfileSerializer

class ProfileDetail(generics.RetrieveAPIView):
    """
    Returns meta data for the given profile id
    """

    queryset = models.Profile
    serializer_class = serializers.FullProfileSerializer

def get_children_data(children, indicator, subindicator):
    return {}

def get_children_profile(profile_id, geography):
    profile = {}
    children_profiles = models.ProfileData.objects.filter(profile_id=profile_id, geography__in=geography.get_children())
    for child_profile in children_profiles:
        for indicator, subindicators in child_profile.data.items():
            indicator_data = profile.setdefault(indicator, {})
            for subindicator in subindicators:
                key = subindicator["key"]
                subindicator_data = indicator_data.setdefault(key, {})
                subindicator_data[child_profile.geography.code] = subindicator["count"]
    return profile

@api_view()
def profile_geography_data(request, profile_id, geography_code):
    profile = models.Profile.objects.get(pk=profile_id)
    try:
        geography = models.Geography.objects.get(code=geography_code)
    except models.Geography.DoesNotExist:
        raise Http404
    except models.Geography.MultipleObjectsReturned as e:
        # TODO this needed because the metro municipalities are considered both districts and local municipalities
        # This dataset-specific code should not be here. I'll move it once I figure out the best course of action
        munis = models.Geography.objects.filter(code=geography_code, level="municipality")
        if munis.count() == 1:
            geography = munis.first()
        else:
            raise e

    profile_data = models.ProfileData.objects.get(profile_id=profile_id, geography=geography)
    data = profile_data.data

    children_profiles = models.ProfileData.objects.filter(profile_id=profile_id, geography__in=geography.get_children())
    children_profile = get_children_profile(profile_id, geography)

    geo_js = AncestorGeographySerializer().to_representation(geography)
    data_js = {}
    key_metrics = []


    for pi in profile.profileindicator_set.order_by("subcategory__category__name", "subcategory__name"):
        indicator = pi.indicator

        if pi.key_metric:
            value = data.get(indicator.name, [{"count": "-"}])[0]
            key_metrics.append({"label": pi.indicator.label, "value": value["count"]})
        else:
            category_js = data_js.setdefault(pi.subcategory.category.name, {})
            subcat_js = category_js.setdefault(pi.subcategory.name, {})
            indicator_data = data.get(pi.name, {})
            subcat_js[pi.label] = indicator_data
            for subindicator in indicator_data:
                if pi.name in children_profile:
                    # TODO change name from children to child_geographies - need to change the UI as well
                    subindicator["children"] = children_profile[pi.name][subindicator["key"]]

    js = {
        "geography": geo_js,
        "key_metrics": key_metrics,
        "indicators": data_js,
    }

    return Response(js)

@api_view()
def search_geography(request):
    """
    Search autocompletion - provides recommendations from place names
    Prioritises higher-level geographies in the results, e.g. 
    Provinces of Municipalities. 

    Querystring parameters
    q - search string
    max-results number of results to be returned [default is 30] 
    """
    
    default_results = 30
    max_results = request.GET.get("max_results", default_results)
    try:
        max_results = int(max_results)
        if max_results <= 0:
            max_results = default_results
    except ValueError:
        max_results = default_results

    q = request.GET.get("q", "")

    geographies = models.Geography.objects.search(q)[0:max_results]

    def sort_key(x):
        exact_match = x.name.lower() == q.lower()
        if exact_match:
            return 0

        else:
            return {
                "province": 1,
                "district": 2,
                "municipality": 3,
                "mainplace": 4,
                "subplace": 5,
                "ward": 6,
            }.get(x.level, 7)

    geogs = sorted(geographies, key=sort_key)
    serializer = serializers.GeographySerializer(geogs, many=True)

    return Response(serializer.data)

@api_view()
def geography_ancestors(request, geography_code):
    """
    Returns parent geographies of the given geographhy code
    Return a 404 HTTP response if the is the code is not found
    """
    geos = models.Geography.objects.filter(code=geography_code)
    if geos.count() == 0:
        raise Http404 

    geography = geos.first()
    geo_js = AncestorGeographySerializer().to_representation(geography)

    return Response(geo_js)
