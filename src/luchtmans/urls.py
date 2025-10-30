from django.urls import path

from .views import WikidataSuggestView, FillFieldsView


urlpatterns = [
    path('wikidata/', WikidataSuggestView.as_view(), name='wikidata'),
    path('fill_fields/', FillFieldsView.as_view(), name='fill_fields'),
]