import decimal

from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, format_html_join
from django.conf import settings
from django.utils import formats

import django_tables2 as tables
from django_tables2.utils import A

from luchtmans.utils import str_to_date
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


class TagsMixin:
    def render_tags(self, record):
        return format_html(' '.join([
            format_html('<span class="badge rounded-pill bg-secondary">{}</span>', tag)
            for tag in record.tags.all()
        ]))


class PersonTable(UUIDMixin, TagsMixin, tables.Table):
    short_name = tables.Column(linkify=('person_detail', [A("pk")]))
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    collection = tables.Column(empty_values=(None), verbose_name="Collection")
    item_count = tables.Column(verbose_name="Number of purchases")
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
            'item_count',
            'number_of_editions',
            'relations',
            'wikidata_id',
            'tags',
        ]

    def render_date_of_birth(self, record):
        return str_to_date(record.date_of_birth)

    def render_date_of_death(self, record):
        return str_to_date(record.date_of_death)

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
        view_collection_url = reverse_lazy('collection_detail', args=[record.collection.id])
        collection_text = f'{record.collection} {record.first_item_year} - {record.last_item_year}'
        if not self.request.user.has_perm('luchtmans.change_collection'):
            return format_html('<a href="{}">{}</a>', view_collection_url, collection_text)

        template = """
            <a href="{}">{}</a>
            <a href="{}" title="{} \'{}\'"><i class="bi bi-pencil"></i></a>
        """
        change_collection_url = reverse_lazy('admin:luchtmans_collection_change',
                                             kwargs={'object_id': record.collection.id})
        return format_html(template, view_collection_url, collection_text, change_collection_url,
                           _("Change collection"), record.collection)

    def render_wikidata_id(self, record):
        return format_html('<a href="{}">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.WIKIDATA_URL.format(record.wikidata_id), record.wikidata_id)


class CollectionTable(UUIDMixin, tables.Table):
    client = tables.Column(linkify=('person_detail', [A("client_id")]), empty_values=(), verbose_name="Short name")
    short_title = tables.Column(linkify=('collection_detail', [A("pk")]), verbose_name="Collection")
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    first_year = tables.Column(empty_values=())
    last_year = tables.Column(empty_values=())
    non_book_count = tables.Column(verbose_name="Number of non-books")
    percentage_non_book = tables.Column(verbose_name="Percentage non-books")
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
            'non_book_count',
            'percentage_non_book',
            'price_total',
            'average_number_of_books_per_year',
            'median_number_of_books_per_year',
            'edition_count',
        ]

    def render_percentage_non_book(self, record):
        decimal_str = f'{record.percentage_non_book:.2f}'
        formatted_decimal_str = formats.number_format(decimal.Decimal(decimal_str))
        return f'{formatted_decimal_str} %'

    def render_price_total(self, record):
        formatted_decimal_str = formats.number_format(decimal.Decimal(record.price_total))
        return f'ƒ {formatted_decimal_str}'


class ItemTable(UUIDMixin, TagsMixin, tables.Table):
    uuid = tables.Column(empty_values=(), verbose_name="", orderable=False)
    collection = tables.Column(linkify=('collection_detail', [A("collection_id")]))
    day_of_week = tables.Column(empty_values=(), orderable=False)
    editions = tables.ManyToManyColumn(linkify_item=('edition_detail', [A("pk")]))

    class Meta:
        model = Item
        attrs = {'class': 'table table-sortable'}
        fields = [
            'transcription_full',
            'uuid',
            'collection',
            'type',
            'non_book',
            'transcription_incomplete',
            'page',
            'date',
            'day_of_week',
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
            'tags',
        ]

    def render_date(self, record):
        return formats.localize(record.date)

    def render_day_of_week(self, record):
        return record.date.strftime('%A')

    def render_date_paid(self, record):
        return formats.localize(record.date)


class ItemsInCollectionTable(ItemTable):
    class Meta(ItemTable.Meta):
        exclude = ('collection',)

    def render_date(self, record):
        return format_html("<a href='{}'>{}</a>",
                           reverse_lazy('items', query={'date': record.date}),
                           formats.localize(record.date))


class EditionTable(UUIDMixin, TagsMixin, tables.Table):
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
            'tags',
        ]

    def render_years_of_publication(self, record):
        return f'{record.year_of_publication_start or "?"} - {record.year_of_publication_end or "?"}'

    def render_stcn_id(self, record):
        return format_html('<a href="{}" title="{}" target="_blank">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.STCN_URL.format(record.stcn_id), _("Show on data.cerl.org/stcn in a new tab/window"), record.stcn_id)

    def render_persons(self, record):
        template = """
            <a href="{}">{}</a>
            <a href="{}" title="{} \'{}\'"><i class="bi bi-pencil"></i></a>
        """
        return format_html(', '.join([
            format_html(template, reverse_lazy('person_detail', kwargs={'pk': person.pk}), person,
                        reverse_lazy('admin:luchtmans_person_change', kwargs={'object_id': person.pk}),
                        _("Change person"), person)
            for person in record.persons.all()
        ]))


class WorkTable(UUIDMixin, TagsMixin, tables.Table):
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
            'tags',
        ]

    def render_viaf_id(self, record):
        return format_html('<a href="{}" title="{}" target="_blank">{} <i class="bi bi-box-arrow-up-right"></i></a>',
                           settings.VIAF_URL.format(record.viaf_id), _("Show on viaf.org in a new tab/window"), record.viaf_id)

    def render_authors(self, record):
        template = """
            <a href="{}">{}</a>
            <a href="{}" title="{} \'{}\'"><i class="bi bi-pencil"></i></a>
        """
        return format_html(', '.join([
            format_html(template, reverse_lazy('person_detail', kwargs={'pk': author.pk}), author,
                        reverse_lazy('admin:luchtmans_person_change', kwargs={'object_id': author.pk}),
                        _("Change author"), author)
            for author in record.authors.all()
        ]))