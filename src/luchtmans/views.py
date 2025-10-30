import requests
import re

from django_select2.views import AutoResponseView
from django.http import JsonResponse
from django.conf import settings
from django.utils import translation


class WikidataSuggestView(AutoResponseView):
    def get(self, request, *args, **kwargs):
        api_key = settings.WIKIDATA_API_KEY
        language_code = translation.get_language()
        term = request.GET.get('term', '')
        page = request.GET.get('page', '1')
        limit = 10

        page = int(page) if re.match(r'^[1-9]\d*$', page) else 1
        offset = (page - 1) * limit

        response = requests.get(settings.WIKIDATA_SUGGEST_URL,
                                params={'q': term, 'language': language_code, 'limit': limit, 'offset': offset},
                                headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}'})

        if response.status_code != requests.codes.ok:
            return JsonResponse({'results': {}, 'more': False})

        results = [
            {'id': item['id'], 'text': f'{item['display-label']['value']} ({item['id']})'}
            for item in response.json().get('results', [])
        ]

        return JsonResponse({
            'results': results,
            'more': len(results) >= limit
        })


class FillFieldsView(AutoResponseView):
    def get(self, request, api_type, *args, **kwargs):
        method = f'get_{api_type}_fillfield_reponse'
        if hasattr(self, method) and callable(getattr(self, method)):
            return JsonResponse(getattr(self, method)(request))
        return JsonResponse({})

    @staticmethod
    def get_wikidata_fillfield_reponse(request):
        api_id = request.GET.get('api_id', "")
        field_name = request.GET.get('field_name', "")
        languages = request.GET.get('languages', "").split(",")

        field_values = {}
        for language_code in languages:
            response = requests.get(settings.WIKIDATA_LABEL_URL.format(api_id, language_code),
                                    headers={'accept': 'application/json',
                                             'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
            if response.status_code != requests.codes.ok:
                continue
            field_values[f'{field_name}_{language_code}'] = response.json()

        return field_values
