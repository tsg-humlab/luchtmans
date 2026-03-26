from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, format_html_join
from django.conf import settings

import django_tables2 as tables
from django_tables2.utils import A

from .models import Person, Collection, Item, Edition, Work


class UUIDMixin:
    def render_uuid(self, record, value):
        model_name = self._meta.model.__name__.lower()
        context = {
            'object': record,
            'url_name_change': f'admin:luchtmans_{model_name}_change' if self.request.user.has_perm(f'luchtmans.change_{model_name}') else '',
            'url_name_delete': f'admin:luchtmans_{model_name}_delete' if self.request.user.has_perm(f'luchtmans.delete_{model_name}') else '',
        }
        return render_to_string('uuid_column.html', context)


class PersonTable(UUIDMixin, tables.Table):
    short_name = tables.Column(linkify=('person_detail', [A("pk")]))
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    collection = tables.Column(empty_values=(None), verbose_name="Collection")
    number_of_editions = tables.Column(empty_values=(), accessor=A("number_of_editions"))
    roles = tables.Column(empty_values=(None))
    relations = tables.Column(
        verbose_name=_("Relations"),
        orderable=False,
        empty_values=(None)
    )
    wikidata_id = tables.Column(verbose_name=_("Wikidata ID"))

    class Meta:
        model = Person
        template_name = "django_tables2/bootstrap5.html"
        attrs = {'class': 'table table-sortable'}
        fields = [
            'short_name',
            'uuid',
            'sex',
            'place_of_birth',
            'date_of_birth',
            'place_of_death',
            'date_of_death',
            'roles',
            'collection',
            'number_of_editions',
            'relations',
            'wikidata_id',
        ]

    def render_relations(self, record):
        person = record
        of_str = ' of'
        relations = []
        for relation in person.to_relations.all():
            relation_of_str = '' if relation.type.name.endswith(of_str) else of_str
            relation_str = format_html(_('{}{} <a href="{}">{}</a>'), str(relation.type).capitalize(), relation_of_str,
                                     relation.second_person.get_absolute_url(), relation.second_person)
            relations.append(relation_str)
        for relation in person.from_relations.all():
            type = str(relation.type)
            type_without_of = type[:-len(of_str)] if type.endswith(of_str) else type
            relation_str = format_html(_('{}: <a href="{}">{}</a>'), type_without_of.capitalize(),
                                     relation.first_person.get_absolute_url(), relation.first_person)
            relations.append(relation_str)
        return format_html_join('\n', '{}<br/>', ((rel,) for rel in relations))

    def render_collection(self, record):
        if not self.request.user.has_perm('luchtmans.change_collection'):
            return format_html('{}', record.collection)

        change_collection_url = reverse_lazy('admin:luchtmans_collection_change',
                                             kwargs={'object_id': record.collection.id})
        return format_html('{} <a href="{}"><i class="bi bi-pencil"></i></a>',
                           record.collection, change_collection_url)

    def render_wikidata_id(self, record):
        return format_html('<a href="{}">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.WIKIDATA_URL.format(record.wikidata_id), record.wikidata_id)


class CollectionTable(UUIDMixin, tables.Table):
    client = tables.Column(linkify=('person_detail', [A("client_id")]), empty_values=(), verbose_name="Short name")
    short_title = tables.Column(linkify=('collection_detail', [A("pk")]), verbose_name="Collection")
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    first_year = tables.Column(empty_values=())
    last_year = tables.Column(empty_values=())
    item_count = tables.Column(empty_values=(), verbose_name="Number of purchases")

    class Meta:
        model = Collection
        attrs = {'class': 'table table-sortable'}
        fields = [
            'client',
            'short_title',
            'uuid',
            'first_year',
            'last_year',
            'item_count',
        ]


class ItemsInCollectionTable(tables.Table):
    page = tables.Column(linkify=('admin:luchtmans_page_change', [A("page__pk")]))

    class Meta:
        model = Item
        attrs = {'class': 'table table-sortable'}
        fields = [
            'transcription_full',
            'type',
            'non_book',
            'transcription_incomplete',
            'page',
            'date',
            'date_paid',
            'editions',
            'edition_uncertain',
            'volumes',
            'number_of_copies',
            'binding',
            'languages',
            'price',
            'price_decimal',
            'notes',
            'work_in_progress',
        ]


class EditionTable(UUIDMixin, tables.Table):
    short_title = tables.Column(linkify=('edition_detail', [A("pk")]))
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    stcn_id = tables.Column(verbose_name=_("STCN ID"))
    years_of_publication = tables.Column(empty_values=(), orderable=False)

    class Meta:
        model = Edition
        attrs = {'class': 'table table-sortable'}
        fields = [
            'short_title',
            'uuid',
            'persons',
            'title',
            'edition_uncertain',
            'places_of_publication',
            'languages',
            'volumes',
            'stcn_id',
            'stcn_genres',
            'work',
            'notes',
            'years_of_publication',
        ]

    def render_years_of_publication(self, record):
        return f'{record.year_of_publication_start or "?"} - {record.year_of_publication_end or "?"}'

    def render_stcn_id(self, record):
        return format_html('<a href="{}">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.STCN_URL.format(record.stcn_id), record.stcn_id)


class WorkTable(UUIDMixin, tables.Table):
    title = tables.Column(linkify=('work_detail', [A("pk")]))
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)

    class Meta:
        model = Work
        attrs = {'class': 'table table-sortable'}
        fields = [
            'title',
            'uuid',
            'authors',
            'uncertain',
            'languages',
            'viaf_id',
            'genre_parisian_category',
            'notes',
        ]

    def render_viaf_id(self, record):
        return format_html('<a href="{}" title="{}" target="_blank">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.VIAF_URL.format(record.viaf_id), _("Show on viaf.org in a new tab/window"), record.viaf_id)

    def render_authors(self, record):
        return format_html(', '.join([
            format_html('{} <a href="{}" title="{} \'{}\'"><i class="bi bi-pencil"></i></a>', author, reverse_lazy('person_detail', kwargs={'pk': author.pk}), _("Change author"), author)
            for author in record.authors.all()
        ]))