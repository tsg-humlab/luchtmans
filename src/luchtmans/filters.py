import django_filters
from django_select2.forms import Select2MultipleWidget
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Person, Place, Country, Religion


# Person filter
class PersonFilter(django_filters.FilterSet):
    short_name = django_filters.Filter(method='short_name_filter')
    surname = django_filters.Filter(method='surname_filter')
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
        ]

    def short_name_filter(self, queryset, name, value):
        if value:
            short_name_q = Q(short_name__icontains=value)
            alternative_short_name_q = Q(alternative_names__short_name__icontains=value)
            return queryset.filter(short_name_q | alternative_short_name_q)
        return queryset

    def surname_filter(self, queryset, name, value):
        if value:
            surname_q = Q(surname__icontains=value)
            alternative_surname_q = Q(alternative_names__surname__icontains=value)
            return queryset.filter(surname_q | alternative_surname_q)
        return queryset

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
