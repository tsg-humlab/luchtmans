import html

import requests
import re

from django_select2.views import AutoResponseView
from django.http import JsonResponse
from django.conf import settings
from django.utils import translation

from .models import Country, Person, Place
from .utils import get_nested_object


def get_wikidata_data(url):
    response = requests.get(url, headers={'accept': 'application/json',
                                          'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
    return response.json() if response.status_code == requests.codes.ok else None


def get_wikidata_statements(id):
    return get_wikidata_data(settings.WIKIDATA_STATEMENTS_URL.format(id))


def get_wikidata_label(id, language='en'):
    return get_wikidata_data(settings.WIKIDATA_LABEL_URL.format(id, language))


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
            {'id': html.escape(item['id']), 'text': self.render_text(item)}
            for item in response.json().get('results', [])
        ]

        return JsonResponse({
            'results': results,
            'more': len(results) >= limit
        })

    @staticmethod
    def render_text(item):
        id = html.escape(item['id'])
        label = html.escape(item['display-label']['value'])
        description = html.escape(item['description']['value'] if item['description'] else '')
        return f"""
            <div>
                <b>{label}</b>
                <span style='color: dimgray; margin-left: auto; margin-right: 0'>{id}</span>
                <br/>
                <small>{description}</small>
            </div>
        """


def get_wikidata_label_translations(api_id, prefix):
    field_values = {}
    for language_code, _ in settings.LANGUAGES:
        response = requests.get(settings.WIKIDATA_LABEL_URL.format(api_id, language_code),
                                headers={'accept': 'application/json',
                                         'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
        if response.status_code != requests.codes.ok:
            continue
        field_values[f'{prefix}{language_code}'] = response.json()
    return field_values


def get_wikidata_label_for_property(data, property, language='en'):
    id = get_nested_object(data, ('statements', property, 0, 'value', 'content'))
    if not id:
        return ''
    resp = requests.get(settings.WIKIDATA_LABEL_URL.format(id, language),
                        headers={'accept': 'application/json',
                                 'Authorization': f'Bearer {settings.WIKIDATA_API_KEY}'})
    return resp.json() if resp.status_code == requests.codes.ok else ''


def get_or_create_object_from_wikidata_id(wikidata_id, property, model):
    if data := get_wikidata_statements(wikidata_id):
        return get_option_from_wikidata_property(data, property, model).get('id', None)
    return None


def create_object_from_wikidata_id(model, wikidata_id):
    if model not in [Place, Country]:
        return None
    field_values = get_wikidata_label_translations(wikidata_id, 'name_')
    field_values['wikidata_id'] = wikidata_id
    if model == Place:
        field_values['country_id'] = get_or_create_object_from_wikidata_id(wikidata_id, 'P17', Country)
    return model.objects.create(**field_values)


def get_option_from_wikidata_property(data, property, model):
    wikidata_id = get_nested_object(data, ('statements', property, 0, 'value', 'content'), None)
    if not wikidata_id:
        return {}
    objects = model.objects.filter(wikidata_id=wikidata_id)
    if objects:
        obj = objects[0]
        return {'text': str(obj), 'id': obj.pk}
    if obj := create_object_from_wikidata_id(model, wikidata_id):
        return {'text': str(obj), 'id': obj.pk}
    return {}


class FillFieldsView(AutoResponseView):
    def get(self, request, fill_field_name, *args, **kwargs):
        method = f'get_{fill_field_name}_fillfield_response'
        if hasattr(self, method) and callable(getattr(self, method)):
            return JsonResponse(getattr(self, method)(request))
        return JsonResponse({})

    @staticmethod
    def get_country_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        return get_wikidata_label_translations(api_id, "name_")

    @staticmethod
    def get_place_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = get_wikidata_label_translations(api_id, "name_")

        if data := get_wikidata_statements(api_id):
            field_values['country'] = get_option_from_wikidata_property(data, 'P17', Country)

        return field_values

    @staticmethod
    def get_person_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = {}
        if data := get_wikidata_statements(api_id):
            field_values['short_name'] = get_wikidata_label(api_id)
            field_values['first_names'] = get_wikidata_label_for_property(data, 'P735')
            field_values['surname'] = get_wikidata_label_for_property(data, 'P734')
            field_values['date_of_birth'] = get_nested_object(data, ('statements', 'P569', 0, 'value', 'content',
                                                                     'time', slice(1, 11)))
            field_values['date_of_death'] = get_nested_object(data, ('statements', 'P570', 0, 'value', 'content',
                                                                     'time', slice(1, 11)), None)
            sex = get_wikidata_label_for_property(data, 'P21')
            field_values['sex'] = getattr(Person.GenderChoices, sex.upper()).value \
                                    if sex and hasattr(Person.GenderChoices, sex.upper()) else None
            field_values['place_of_birth'] = get_option_from_wikidata_property(data, 'P19', Place)
            field_values['place_of_death'] = get_option_from_wikidata_property(data, 'P20', Place)

        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values

    @staticmethod
    def get_address_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = {'description': get_wikidata_label(api_id)}
        # TODO Get/create Housenumber, Street, Place and Country (problem: the info is hard to get from WikiData)
        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values

    @staticmethod
    def get_street_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = {}
        field_values['name'] = get_wikidata_label(api_id)
        # TODO Create Place en Country (problem: streets are often linked to a municipality instead of a city)
        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values
