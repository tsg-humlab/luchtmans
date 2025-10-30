import requests

from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils import translation

from modeltranslation.admin import TranslationAdmin

from .models import (Country, Place, Street, Address, Person, PersonPersonRelation, RelationType, PeriodOfResidence,
                     Religion, PersonReligion, UniqueNameModel, Language, GenreParisianCategory, Work,
                     PersonWorkRelationRole, PersonWorkRelation, Format, STCNGenre, Edition, PersonEditionRelationRole,
                     PersonEditionRelation, Collection, ItemType, Page, Binding, Item)
from .forms import ApiSelectWidget, ApiInfo


@admin.register(Country)
class CountryAdmin(TranslationAdmin):
    search_fields = ["name"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if not obj:
            form.base_fields['wikidata_id'].widget = ApiSelectWidget(
                data_view='wikidata',
                api_info=ApiInfo(obj, 'wikidata_id', settings.WIKIDATA_URL, 'Wikidata', fill_field_name='name'),
            )
            return form

        language_code = translation.get_language()
        api_key = settings.WIKIDATA_API_KEY
        response = requests.get(settings.WIKIDATA_LABEL_URL.format(obj.wikidata_id, language_code),
                                headers={'accept': 'application/json', 'Authorization': f'Bearer {api_key}'})
        text = f'{str(response.json())} ({obj.wikidata_id})' \
                    if response.status_code == requests.codes.ok \
                    else obj.wikidata_id

        form.base_fields['wikidata_id'].widget = ApiSelectWidget(
            data_view='wikidata',
            choices=[(obj.wikidata_id, text)],
            api_info=ApiInfo(obj, 'wikidata_id', settings.WIKIDATA_URL, 'Wikidata', fill_field_name='name')
        )
        return form


@admin.register(Place)
class PlaceAdmin(TranslationAdmin):
    list_display = ["name", "country"]
    search_fields = ["name", "country__name"]
    list_filter = ["country"]
    autocomplete_fields = ["country"]


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ["name", "place", "country"]
    search_fields = ["name", "place__name"]
    list_filter = ["place"]
    autocomplete_fields = ["place"]

    def country(self, obj):
        return obj.place.country


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["address", "place", "description", "streetname_old"]
    search_fields = ["description", "streetname_old", "house_number"]
    list_filter = ["street__place__name"]
    autocomplete_fields = ["street"]

    @admin.display(description=_("address"))
    def address(self, obj):
        return f'{obj.street} {obj.house_number}'

    @admin.display(description=_("place"), ordering='street__place')
    def place(self, obj):
        return obj.street.place


class RelatedPersonInline(admin.TabularInline):
    model = PersonPersonRelation
    fields = ["types", "to_person"]
    autocomplete_fields = ["types", "to_person"]
    extra = 0
    verbose_name = _("Related person")
    fk_name = "from_person"


class ReligionInline(admin.TabularInline):
    model = PersonReligion
    extra = 0
    verbose_name = _("Religious affiliation")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = [
        "short_name",
        "sex",
        "place_of_birth", "date_of_birth",
        "place_of_death", "date_of_death",
        "wikidata_link"
    ]
    search_fields = ["short_name", "surname", "first_names"]
    autocomplete_fields = ["place_of_birth", "place_of_death"]
    list_filter = ["sex", "place_of_birth", "place_of_death", "religious_affiliation"]
    inlines = [RelatedPersonInline, ReligionInline]

    def wikidata_link(self, obj):
        wikidata_id = html.escape(obj.wikidata_id)
        return mark_safe(f'<a href="https://www.wikidata.org/wiki/{wikidata_id}">{wikidata_id}</a>')


@admin.register(PersonPersonRelation)
class PersonPersonRelationAdmin(TranslationAdmin):
    list_display = ["from_person", "type", "to_person"]
    search_fields = ["from_person__short_name", "to_person__short_name", "types__text"]
    autocomplete_fields = ["from_person", "to_person", "types"]

    def type(self, obj):
        return ", ".join([_('is {type} of').format(type=type.text) for type in obj.types.all()])


@admin.register(RelationType)
class RelationTypeAdmin(admin.ModelAdmin):
    search_fields = ["text", "reverse"]
    autocomplete_fields = ["reverse"]


@admin.register(PeriodOfResidence)
class PeriodOfResidenceAdmin(admin.ModelAdmin):
    search_fields = ["person__short_name", "address__street__name", "address__street__place__name"]
    autocomplete_fields = ["person", "address"]


@admin.register(Religion)
class ReligionAdmin(TranslationAdmin):
    search_fields = ["name"]

# Register empty admin classes in one go
for model in [PersonWorkRelation, Format, PersonEditionRelation, Collection, ItemType, Page, Binding, Item]:
    base_class = TranslationAdmin if model.__base__ == UniqueNameModel else admin.ModelAdmin
    admin_class = type(model.__name__+'Admin', (base_class,), {})
    admin.site.register(model, admin_class)


@admin.register(Language)
class LanguageAdmin(TranslationAdmin):
    search_fields = ['name']


@admin.register(GenreParisianCategory)
class GenreParisianCategoryAdmin(TranslationAdmin):
    search_fields = ['name']


@admin.register(PersonWorkRelationRole)
class PersonWorkRelationRoleAdmin(TranslationAdmin):
    search_fields = ['name']


class AuthorInline(admin.TabularInline):
    model = PersonWorkRelation
    fields = ["work", "person", "role"]
    autocomplete_fields = ["person", "role"]
    extra = 0
    verbose_name = _("author")
    verbose_name_plural = _("authors")


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors_list', 'uncertain', 'language_list', 'viaf_id', 'genre_parisian_category', 'notes']
    search_fields = ['title']
    list_filter = ['uncertain', 'languages', 'genre_parisian_category']
    autocomplete_fields = ['languages', 'genre_parisian_category']
    inlines = [AuthorInline]

    @admin.display(description=_("authors"))
    def authors_list(self, obj):
        return ", ".join(obj.authors.values_list('short_name', flat=True))

    @admin.display(description=_("languages"))
    def language_list(self, obj):
        return ", ".join(obj.languages.values_list('name', flat=True))


@admin.register(STCNGenre)
class STCNGenreAdmin(TranslationAdmin):
    search_fields = ['name']


class PersonInline(admin.TabularInline):
    model = PersonEditionRelation
    fields = ["edition", "person", "role"]
    autocomplete_fields = ["person", "role"]
    extra = 0
    verbose_name = _("person")
    verbose_name_plural = _("persons")


@admin.register(PersonEditionRelationRole)
class PersonEditionRelationRoleAdmin(TranslationAdmin):
    search_fields = ['name']


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ['title', 'person_list', 'edition_uncertain', 'years', 'place_of_publication_list', 'language_list',
                    'volumes', 'stcn_genre_list', 'notes']
    search_fields = ['short_title', 'title']
    list_filter = ['edition_uncertain', 'places_of_publication', 'languages', 'stcn_genres']
    autocomplete_fields = ['places_of_publication', 'languages', 'stcn_genres', 'work']
    inlines = [PersonInline]

    @admin.display(description=_("persons"))
    def person_list(self, obj):
        return ", ".join([f'{relation.person} ({relation.role})' for relation in obj.persons.through.objects.all()])

    @admin.display(description=_("years"))
    def years(self, obj):
        return f'{obj.year_of_publication_start} - {obj.year_of_publication_end}'

    @admin.display(description=_("places"))
    def place_of_publication_list(self, obj):
        return ", ".join(obj.places_of_publication.values_list('name', flat=True))

    @admin.display(description=_("languages"))
    def language_list(self, obj):
        return ", ".join(obj.languages.values_list('name', flat=True))

    @admin.display(description=_("STCN genres"))
    def stcn_genre_list(self, obj):
        return ", ".join(obj.stcn_genres.values_list('name', flat=True))
