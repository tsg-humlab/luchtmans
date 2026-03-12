from django.urls import path
from django.views.generic.base import RedirectView

from .views import WikidataSuggestView, FillFieldsView, ObjectExistsWikidataView


urlpatterns = [
    path('', RedirectView.as_view(url='/admin')),
    path('wikidata/', WikidataSuggestView.as_view(), name='wikidata'),
    path('fill_fields/<fill_field_name>/', FillFieldsView.as_view(), name='fill_fields'),
    path('object_exists_wikidata/<model_name>/<wikidata_id>/', ObjectExistsWikidataView.as_view(), name='object_exists_wikidata'),
]