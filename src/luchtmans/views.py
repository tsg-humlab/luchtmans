from django_select2.views import AutoResponseView
from django.http import JsonResponse


class WikidataSuggestView(AutoResponseView):
    def get(self, request, *args, **kwargs):
        results = [
            {'id': 'Q55', 'text': 'The Netherlands (Q55)'},
            {'id': 'Q99999', 'text': 'The Kingdom of the Netherlands (Q99999)'},
        ]
        more = False
        return JsonResponse({
            'results': results,
            'more': more
        })