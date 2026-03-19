from django.urls import path
from django.views.generic.base import RedirectView, TemplateView

from .views import WikidataSuggestView, FillFieldsView, ObjectExistsWikidataView, PersonTableView, PersonDetailView, \
    CollectionTableView, CollectionDetailView, EditionTableView, EditionDetailView, WorkTableView, WorkDetailView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='about', permanent=False)),
    path('wikidata/', WikidataSuggestView.as_view(), name='wikidata'),
    path('fill_fields/<fill_field_name>/', FillFieldsView.as_view(), name='fill_fields'),
    path('object_exists_wikidata/<model_name>/<wikidata_id>/', ObjectExistsWikidataView.as_view(), name='object_exists_wikidata'),
    path('about', TemplateView.as_view(template_name="about.html"), name='about'),
    path('persons', PersonTableView.as_view(), name='persons'),
    path('person/<uuid:pk>', PersonDetailView.as_view(), name='person_detail'),
    path('collections', CollectionTableView.as_view(), name='collections'),
    path('collection/<uuid:pk>', CollectionDetailView.as_view(), name='collection_detail'),
    path('editions', EditionTableView.as_view(), name='editions'),
    path('edition/<uuid:pk>', EditionDetailView.as_view(), name='edition_detail'),
    path('works', WorkTableView.as_view(), name='works'),
    path('work/<uuid:pk>', WorkDetailView.as_view(), name='work_detail'),
]