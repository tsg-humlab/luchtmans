import html
import requests
from django.db.models import Count, OuterRef, Subquery, Q, Sum, F, Case, When, Value

from django.views.generic import ListView, DetailView
from django_select2.views import AutoResponseView
from django.http import JsonResponse
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.urls import reverse_lazy
from requests import Response

import django_tables2

from .models import Country, Person, Place, Edition, Collection, Item, Work, Page, PeriodOfResidence
from .filters import PersonFilter, CollectionFilter, EditionFilter, WorkFilter, ItemFilter
from .tables import PersonTable, CollectionTable, ItemsInCollectionTable, EditionTable, WorkTable, ItemTable
from .utils import get_nested_object, SubqueryMedian
from .wikidata_api import get_wikidata_statements, get_wikidata_label
from .apps import LuchtmansConfig


def request_wikidata_suggest(term: str, page: int=1, limit: int=10) -> Response:
    api_key = settings.WIKIDATA_API_KEY
    language_code = translation.get_language()
    offset = (page - 1) * limit

    return requests.get(settings.WIKIDATA_SUGGEST_URL,
                        params={'q': term, 'language': language_code, 'limit': limit, 'offset': offset},
                        headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}'})


class WikidataSuggestView(AutoResponseView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        page = request.GET.get('page', '1')
        page = int(page) if page.isdigit() else 1
        limit = 10
        response = request_wikidata_suggest(term, page, limit)

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
    id = get_nested_object(data, ('statements', property, 0, 'value', 'content'), None)
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
    if data := get_wikidata_statements(wikidata_id):
        latitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
        longitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
        field_values['location'] = f'{{ "type": "Point", "coordinates": [ {longitude}, {latitude} ] }}'  # Leaflet format
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
        field_values = get_wikidata_label_translations(api_id, "name_")
        if data := get_wikidata_statements(api_id):
            latitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
            longitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
            field_values['location'] = f'{{ "type": "Point", "coordinates": [ {longitude}, {latitude} ] }}'  # Leaflet format
        return field_values

    @staticmethod
    def get_place_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = get_wikidata_label_translations(api_id, "name_")

        if data := get_wikidata_statements(api_id):
            field_values['country'] = get_option_from_wikidata_property(data, 'P17', Country)
            latitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
            longitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
            field_values['location'] = f'{{ "type": "Point", "coordinates": [ {longitude}, {latitude} ] }}'  # Leaflet format

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
        field_values = {}
        if data := get_wikidata_statements(api_id):
            field_values['description'] = get_wikidata_label(api_id)
            latitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
            longitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
            field_values['location'] = f'{{ "type": "Point", "coordinates": [ {longitude}, {latitude} ] }}'  # Leaflet format
        print(field_values)
        # TODO Get/create Housenumber, Street, Place and Country (problem: the info is hard to get from WikiData)
        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values

    @staticmethod
    def get_street_wikidata_fillfield_response(request):
        api_id = request.GET.get('api_id', "")
        field_values = {}
        field_values['name'] = get_wikidata_label(api_id)
        if data := get_wikidata_statements(api_id):
            latitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'latitude')), 6)
            longitude = round(get_nested_object(data, ('statements', 'P625', 0, 'value', 'content', 'longitude')), 6)
            field_values['location'] = f'{{ "type": "Point", "coordinates": [ {longitude}, {latitude} ] }}'  # Leaflet format
        # TODO Create Place en Country (problem: streets are often linked to a municipality instead of a city)
        return {k:v for k,v in field_values.items() if v}  # Leave out items with empty values


class ObjectExistsWikidataView(AutoResponseView):
    """Returns whether an object exists given the model name and Wikidata ID"""
    def get(self, request, model_name, wikidata_id):
        model = apps.get_model(app_label=LuchtmansConfig.name, model_name=model_name)
        return JsonResponse({
            'exists': model.objects.filter(wikidata_id=wikidata_id).exists()
        })


class PersonTableView(ListView):
    model = Person
    template_name = 'generic_list.html'


    def get_queryset(self):
        items_in_collection = Item.objects.filter(collection__client_id=OuterRef('pk'))
        first_item_year = items_in_collection.order_by('date').values("date__year")[:1]
        last_item_year = items_in_collection.order_by('-date').values("date__year")[:1]
        return (Person.objects.distinct()
                .select_related('collection', 'place_of_birth', 'place_of_death')
                .annotate(item_count=Count('collection__item'))
                .annotate(number_of_editions=Count(Edition.objects
                                                   .filter(work__personworkrelation__person=OuterRef('pk'))
                                                   .values('pk')))
                .annotate(first_item_year=first_item_year, last_item_year=last_item_year))

    def get_context_data(self, **kwargs):
        context = super(PersonTableView, self).get_context_data(**kwargs)
        filter = PersonFilter(self.request.GET, queryset=self.get_queryset())

        table = PersonTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        context['object_name'] = "person"
        context['add_url'] = reverse_lazy('admin:luchtmans_person_add') \
                                if self.request.user.has_perm('luchtmans.add_person') else None

        context['per_page_choices'] = [25, 50, 100]

        return context


class PersonDetailView(DetailView):
    model = Person

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editions'] = Edition.objects.filter(work__personworkrelation__person=self.get_object())
        context['periods_of_residence'] = PeriodOfResidence.objects.filter(person=self.get_object())
        return context


class CollectionTableView(ListView):
    model = Collection
    template_name = 'generic_list.html'

    def get_queryset(self):
        items_in_collection = Item.objects.filter(collection_id=OuterRef('pk'))
        first_item_year = items_in_collection.order_by('date').values("date__year")[:1]
        last_item_year = items_in_collection.order_by('-date').values("date__year")[:1]
        year_counts = (items_in_collection.values('date__year').annotate(year_count=Count('date__year'))
                       .values('year_count'))
        return (
            Collection.objects.distinct()
            .annotate(first_year=Subquery(first_item_year))
            .annotate(last_year=Subquery(last_item_year))
            .annotate(item_count=Count('item'))
            .annotate(non_book_count=Count('item', filter=Q(item__non_book=True)))
            .annotate(percentage_non_book=Case(When(item_count=0, then=Value(0.0)),
                                               default=100.0 * F('non_book_count') / F('item_count')))
            .annotate(price_total=Sum('item__price_decimal'))
            .annotate(year_count=Count('item__date__year', distinct=True))
            .annotate(average_number_of_books_per_year=Case(When(year_count=0, then=Value(0.0)),
                                                            default=1.0 * F('item_count') / F('year_count')))
            .annotate(median_number_of_books_per_year=SubqueryMedian(year_counts))
            .annotate(edition_count=Count('client__work__edition', distinct=True))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = CollectionFilter(self.request.GET, queryset=self.get_queryset())

        table = CollectionTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        context['object_name'] = "collection"
        context['add_url'] = reverse_lazy('admin:luchtmans_collection_add') \
                                if self.request.user.has_perm('luchtmans.add_collection') else None

        context['per_page_choices'] = [25, 50, 100]

        return context


class CollectionDetailView(DetailView):
    model = Collection

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        item_table = ItemsInCollectionTable(Item.objects.filter(collection=self.get_object()))
        django_tables2.RequestConfig(self.request, ).configure(item_table)
        context['item_table'] = item_table

        first_year = Item.objects.filter(page=OuterRef('pk')).order_by('date__year').values('date__year')[:1]
        last_year = Item.objects.filter(page=OuterRef('pk')).order_by('-date__year').values('date__year')[:1]
        context['pages'] = (Page.objects.filter(item__collection=self.get_object()).distinct()
                            .annotate(first_year=first_year).annotate(last_year=last_year))

        return context


class EditionTableView(ListView):
    model = Edition
    template_name = 'generic_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = EditionFilter(self.request.GET, queryset=self.get_queryset())

        table = EditionTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        context['object_name'] = "edition"
        context['add_url'] = reverse_lazy('admin:luchtmans_edition_add') \
                                if self.request.user.has_perm('luchtmans.add_edition') else None

        context['per_page_choices'] = [25, 50, 100]

        return context


class EditionDetailView(DetailView):
    model = Edition


class WorkTableView(ListView):
    model = Work
    template_name = 'generic_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = WorkFilter(self.request.GET, queryset=self.get_queryset())

        table = WorkTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        context['object_name'] = "work"
        context['add_url'] = reverse_lazy('admin:luchtmans_work_add') \
                                if self.request.user.has_perm('luchtmans.add_work') else None

        context['per_page_choices'] = [25, 50, 100]

        return context


class WorkDetailView(DetailView):
    model = Work


class ItemTableView(ListView):
    model = Item
    template_name = 'generic_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter = ItemFilter(self.request.GET, queryset=self.get_queryset())

        table = ItemTable(filter.qs)
        django_tables2.RequestConfig(self.request, ).configure(table)

        context['filter'] = filter
        context['table'] = table

        context['object_name'] = "Item"
        context['add_url'] = reverse_lazy('admin:luchtmans_item_add') \
            if self.request.user.has_perm('luchtmans.add_item') else None

        context['per_page_choices'] = [25, 50, 100]

        return context