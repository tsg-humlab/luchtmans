import django_filters
from django_select2.forms import Select2MultipleWidget
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from bootstrap_datepicker_plus.widgets import DatePickerInput

from .models import Person, Place, Country, Religion, Collection, Item, Edition, Language, Work, PersonTag, EditionTag, \
    WorkTag, ItemTag
from .utils import and_or_to_q


# Person filter
class PersonFilter(django_filters.FilterSet):
    short_name = django_filters.Filter(method='short_name_filter')
    surname = django_filters.Filter(method='short_name_filter')
    sex = django_filters.MultipleChoiceFilter(
        choices=Person.GenderChoices,
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},)
    )
    place_of_birth = django_filters.ModelMultipleChoiceFilter(
        label=mark_safe(_("Place of birth")),
        queryset=Place.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},)
    )
    country_of_birth = django_filters.ModelMultipleChoiceFilter(
        label="Country of birth",
        queryset=Country.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},),
        field_name='place_of_birth__country',
    )
    place_of_death = django_filters.ModelMultipleChoiceFilter(
        label=mark_safe(_("Place of death")),
        queryset=Place.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},)
    )
    country_of_death = django_filters.ModelMultipleChoiceFilter(
        label="Country of death",
        queryset=Country.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},),
        field_name='place_of_death__country',
    )
    religious_affiliation = django_filters.ModelMultipleChoiceFilter(
        label="Religious affiliation",
        queryset=Religion.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='religiousaffiliation__religion',
    )
    place_of_residence = django_filters.ModelMultipleChoiceFilter(
        label=mark_safe(_("Place of residence")),
        queryset=Place.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='periodofresidence__address__street__place',
    )
    country_of_residence = django_filters.ModelMultipleChoiceFilter(
        label="Country of residence",
        queryset=Country.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},),
        field_name='periodofresidence__address__street__place__country',
    )
    related_to = django_filters.ModelMultipleChoiceFilter(
        label="Related to",
        queryset=Person.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        method='related_to_filter'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        label="Tags",
        queryset=PersonTag.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='tags__name',
    )

    class Meta:
        model = Person
        fields = [
            'short_name',
            'sex',
            'place_of_birth',
            'country_of_birth',
            'date_of_birth',
            'place_of_death',
            'country_of_death',
            'date_of_death',
            'religious_affiliation',
            'related_to',
            'tags',
        ]

    def short_name_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'short_name'))

    def surname_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'surname'))

    def related_to_filter(self, queryset, name, value):
        if value:
            first_person_query = Q(to_relations__to_person__in=value)
            second_person_query = Q(from_relations__from_person__in=value)
            return queryset.filter(first_person_query | second_person_query).distinct()
        return queryset

    def nature_of_relation_filter(self, queryset, name, value):
        if value:
            first_person_query = Q(to_relations__types__in=value)
            second_person_query = Q(from_relations__types__in=value)
            return queryset.filter(first_person_query | second_person_query).distinct()
        return queryset

class CollectionFilter(django_filters.FilterSet):
    short_title = django_filters.CharFilter(label=mark_safe(_("Short title")), method='short_title_filter')
    all_headers = django_filters.CharFilter(label=mark_safe(_("Headers")), method='all_headers_filter')
    client = django_filters.ModelMultipleChoiceFilter(
        label="Client",
        queryset=Person.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"},),
        field_name='client',
    )
    notes = django_filters.CharFilter(label=mark_safe(_("Notes")), method='notes_filter')

    class Meta:
        model = Collection
        fields = [
            'short_title',
            'all_headers',
            'client',
            'notes',
        ]

    def short_title_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'short_title'))

    def all_headers_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'all_headers'))

    def notes_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'notes'))


class EditionFilter(django_filters.FilterSet):
    short_title = django_filters.Filter(method='short_title_filter')
    persons = django_filters.ModelMultipleChoiceFilter(
        queryset=Person.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='persons',
    )
    title = django_filters.Filter(method='title_filter')
    places_of_publication = django_filters.ModelMultipleChoiceFilter(
        queryset=Place.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='places_of_publication',
    )
    languages = django_filters.ModelMultipleChoiceFilter(
        queryset=Language.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='languages',
    )
    volumes = django_filters.Filter(method='volumes_filter')
    notes = django_filters.Filter(method='notes_filter')
    tags = django_filters.ModelMultipleChoiceFilter(
        label="Tags",
        queryset=EditionTag.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='tags__name',
    )

    class Meta:
        model = Edition
        fields = [
            'short_title',
            'persons',
            'title',
            'edition_uncertain',
            'places_of_publication',
            'languages',
            'volumes',
            'stcn_genres',
            'work',
            'notes',
            'year_of_publication_start',
            'year_of_publication_end',
            'tags',
        ]

    def short_title_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'short_title'))

    def title_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'title'))

    def volumes_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'volumes'))

    def notes_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'notes'))


class WorkFilter(django_filters.FilterSet):
    title = django_filters.Filter(method='title_filter')
    authors = django_filters.ModelMultipleChoiceFilter(
        label=mark_safe(_("Authors")),
        queryset=Person.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='authors',
    )
    languages = django_filters.ModelMultipleChoiceFilter(
        queryset=Language.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='languages',
    )
    notes = django_filters.Filter(method='notes_filter')
    tags = django_filters.ModelMultipleChoiceFilter(
        label="Tags",
        queryset=WorkTag.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='tags__name',
    )

    class Meta:
        model = Work
        fields = [
            'title',
            'uncertain',
            'authors',
            'languages',
            'notes',
            'tags',
        ]

    def title_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'title'))

    def notes_filter(self, queryset, name, value):
        return queryset.filter(and_or_to_q(value.strip(), 'notes'))


class ItemFilter(django_filters.FilterSet):
    collections = django_filters.ModelMultipleChoiceFilter(
        label=mark_safe(_("Collections")),
        queryset=Collection.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}),
        field_name='collection',
    )
    date = django_filters.DateFilter(widget=DatePickerInput())
    tags = django_filters.ModelMultipleChoiceFilter(
        label="Tags",
        queryset=ItemTag.objects.all(),
        widget=Select2MultipleWidget(attrs={'data-placeholder': "Select multiple"}, ),
        field_name='tags__name',
    )

    class Meta:
        model = Item
        fields = [
            'collections',
            'date',
            'tags',
        ]

