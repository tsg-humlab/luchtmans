from django.urls import path

from .views import WikidataSuggestView


urlpatterns = [
    path('wikidata/', WikidataSuggestView.as_view(), name='wikidata'),
]